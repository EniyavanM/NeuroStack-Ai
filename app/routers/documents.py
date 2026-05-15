"""RAG document routes."""

from fastapi import APIRouter, File, UploadFile

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.common import APIResponse, success_response
from app.schemas.document import DocumentAskRequest
from app.services import rag_service

router = APIRouter(prefix="/documents", tags=["Documents (RAG)"])


@router.post("/upload", response_model=APIResponse)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
):
    doc = await rag_service.upload_document(db, current_user, file)
    return success_response(
        data={
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "chunk_count": doc.chunk_count,
            "upload_time": doc.upload_time.isoformat(),
        },
        message="Document uploaded and indexed",
    )


@router.post("/ask", response_model=APIResponse)
async def ask_document(payload: DocumentAskRequest, current_user: CurrentUser, db: DbSession):
    answer, sources = await rag_service.ask_documents(
        db, current_user, payload.question, payload.document_id, payload.top_k
    )
    return success_response(
        data={"answer": answer, "sources": sources},
        message="Question answered from documents",
    )


@router.get("/list", response_model=APIResponse)
async def list_documents(current_user: CurrentUser, db: DbSession):
    docs = await rag_service.list_documents(db, current_user)
    data = [
        {
            "id": d.id,
            "filename": d.filename,
            "original_filename": d.original_filename,
            "chunk_count": d.chunk_count,
            "upload_time": d.upload_time.isoformat(),
        }
        for d in docs
    ]
    return success_response(data=data)


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(document_id: int, current_user: CurrentUser, db: DbSession):
    await rag_service.delete_document(db, current_user, document_id)
    return success_response(message="Document deleted")
