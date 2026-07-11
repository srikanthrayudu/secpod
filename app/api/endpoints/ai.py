import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.services.ai import AIService
from app.services.test_run_service import TestRunService
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    use_rag: bool = True

class DocRequest(BaseModel):
    text: str
    topic: str | None = None

class DraftTestCaseRequest(BaseModel):
    requirement_text: str

class SummarizeFailuresRequest(BaseModel):
    release_id: uuid.UUID
    limit: int = 50

@router.post("/chat")
async def chat_completion(
    request: ChatRequest,
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_active_user)
):
    if request.use_rag:
        response = await ai_service.get_response_with_rag(request.prompt, request.system_prompt)
    else:
        response = await ai_service.provider.generate_response(request.prompt, request.system_prompt)
    return {"response": response}

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_active_user)
):
    async def event_generator():
        if request.use_rag:
            async for chunk in ai_service.stream_response_with_rag(request.prompt, request.system_prompt):
                yield chunk
        else:
            async for chunk in ai_service.provider.stream_response(request.prompt, request.system_prompt):
                yield chunk
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/vector-db/document")
async def add_document(
    request: DocRequest,
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_active_user)
):
    ai_service.vector_db.add_document(request.text, {"topic": request.topic or "general"})
    return {"message": "Document added to vector database successfully."}

@router.post("/draft-test-case")
async def draft_test_case(
    request: DraftTestCaseRequest,
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_qa_engineer)
):
    return await ai_service.draft_test_case(request.requirement_text)

@router.post("/summarize-failures")
async def summarize_failures(
    request: SummarizeFailuresRequest,
    ai_service: AIService = Depends(deps.get_ai_service),
    db = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_lead)
):
    test_run_service = TestRunService(db)
    failed_runs = await test_run_service.get_test_runs(
        release_id=request.release_id,
        status="failed",
        limit=request.limit
    )
    logs = [run.logs for run in failed_runs if run.logs]
    return await ai_service.summarize_failures(logs)

