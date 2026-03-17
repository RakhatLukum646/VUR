"""Translation API endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["translation"])

# Module-level limiter — mirrors the one attached to app.state in main.py.
# slowapi resolves limits against the shared state automatically.
_limiter = Limiter(key_func=get_remote_address)


class TranslationRequest(BaseModel):
    sign_sequence: List[str] = Field(..., description="List of detected signs")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    context: Optional[str] = Field(None, description="Previous context override")
    language: str = Field("ru", description="Target language code")


class TranslationResponse(BaseModel):
    translation: str
    confidence: float
    session_id: str
    processing_time_ms: int
    alternatives: Optional[List[str]] = None
    fallback: bool = False


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    last_activity: str
    context: str
    history: List[dict]


class CreateSessionResponse(BaseModel):
    session_id: str
    message: str


def _get_builder(request: Request):
    """Retrieve the global SentenceBuilder stored in app state."""
    builder = getattr(request.app.state, "sentence_builder", None)
    if builder is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SentenceBuilder not initialized yet",
        )
    return builder


@router.post("/translate", response_model=TranslationResponse)
@_limiter.limit("30/minute")
async def translate_signs(request: Request, body: TranslationRequest):
    """Translate sign sequence to natural language."""
    builder = _get_builder(request)

    try:
        session_id = body.session_id
        if not session_id:
            session_id = builder.create_session()
            logger.info(f"Auto-created session: {session_id}")

        result = await builder.process(
            sign_sequence=body.sign_sequence,
            session_id=session_id,
            context=body.context,
            language=body.language,
        )

        return TranslationResponse(**result)

    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}",
        )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: Request):
    builder = _get_builder(request)
    session_id = builder.create_session()
    return CreateSessionResponse(
        session_id=session_id,
        message="Session created successfully",
    )


@router.get("/context/{session_id}", response_model=SessionResponse)
async def get_context(session_id: str, request: Request):
    builder = _get_builder(request)
    session_data = builder.get_session_context(session_id)

    if "error" in session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return SessionResponse(**session_data)


@router.delete("/context/{session_id}")
async def clear_session(session_id: str, request: Request):
    builder = _get_builder(request)
    success = builder.clear_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {"message": "Session cleared", "session_id": session_id}
