"""RAG pipeline: PDF ingest, chunking, ChromaDB retrieval."""

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document
from app.models.user import User
from app.services.llm import generate_reply

_embeddings = None
_chroma_client = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        settings = get_settings()
        _embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    return _embeddings


def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        settings = get_settings()
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def _collection_name(user_id: int, doc_id: int) -> str:
    return f"user_{user_id}_doc_{doc_id}"


def _extract_pdf_text(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from PDF")
    return text


async def upload_document(db: AsyncSession, user: User, file: UploadFile) -> Document:
    settings = get_settings()
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.max_upload_mb}MB limit",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.pdf"
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)

    from langchain.text_splitter import RecursiveCharacterTextSplitter

    text = _extract_pdf_text(str(file_path))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(text)

    doc = Document(
        user_id=user.id,
        filename=stored_name,
        original_filename=file.filename,
        file_path=str(file_path),
        embedding_path=_collection_name(user.id, 0),
        chunk_count=len(chunks),
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    collection_name = _collection_name(user.id, doc.id)
    doc.embedding_path = collection_name
    embeddings = _get_embeddings()
    vectors = embeddings.embed_documents(chunks)
    chroma = _get_chroma()
    collection = chroma.get_or_create_collection(name=collection_name)
    ids = [f"{doc.id}_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=[{"document_id": doc.id, "chunk_index": i} for i in range(len(chunks))],
    )
    await db.flush()
    return doc


async def list_documents(db: AsyncSession, user: User) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == user.id).order_by(Document.upload_time.desc())
    )
    return list(result.scalars().all())


async def delete_document(db: AsyncSession, user: User, document_id: int) -> None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        chroma = _get_chroma()
        chroma.delete_collection(doc.embedding_path)
    except Exception:
        pass

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.execute(delete(Document).where(Document.id == document_id))


async def ask_documents(
    db: AsyncSession,
    user: User,
    question: str,
    document_id: int | None,
    top_k: int = 4,
) -> tuple[str, list[str]]:
    if document_id:
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user.id)
        )
        docs = [result.scalar_one_or_none()]
        if docs[0] is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    else:
        docs = await list_documents(db, user)
        if not docs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents uploaded")

    embeddings = _get_embeddings()
    query_vector = embeddings.embed_query(question)
    chroma = _get_chroma()
    retrieved_chunks: list[str] = []

    for doc in docs:
        if doc is None:
            continue
        try:
            collection = chroma.get_collection(doc.embedding_path)
            results = collection.query(query_embeddings=[query_vector], n_results=top_k)
            if results and results.get("documents"):
                retrieved_chunks.extend(results["documents"][0])
        except Exception:
            continue

    if not retrieved_chunks:
        return "No relevant context found in your documents.", []

    context = "\n\n---\n\n".join(retrieved_chunks[: top_k * 2])
    system = (
        "Answer the question using only the provided context. "
        "If the answer is not in the context, say you don't know."
    )
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = await generate_reply(prompt, system_prompt=system)
    return answer, retrieved_chunks[:top_k]
