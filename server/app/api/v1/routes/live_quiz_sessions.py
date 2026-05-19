from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from server.app.db.core.connection import (
    get_live_quiz_sessions_collection,
    get_quizzes_v2_collection,
)
from server.app.db.models.user_models import UserOut
from server.app.db.schemas.quiz_schemas import (
    AccessCodeCreateRequest,
    AccessCodeResponse,
    QuizAccessPreview,
)
from server.app.dependancies import get_verified_user
from server.app.db.v2.repositories.live_quiz_session_repository import (
    LiveQuizSessionRepository,
)
from server.app.schemas.live_quiz_session import (
    LiveQuizAnalyticsRow,
    LiveQuizSessionState,
    SaveLiveQuizAnswerRequest,
    SaveLiveQuizAnswerResponse,
    StartLiveQuizSessionRequest,
    StartLiveQuizSessionResponse,
    SubmitLiveQuizSessionResponse,
)
from server.app.services.live_quiz_session_service import LiveQuizSessionService


router = APIRouter()


def get_live_quiz_service(
    quizzes_v2_collection: AsyncIOMotorCollection = Depends(get_quizzes_v2_collection),
    sessions_collection: AsyncIOMotorCollection = Depends(
        get_live_quiz_sessions_collection
    ),
) -> LiveQuizSessionService:
    repository = LiveQuizSessionRepository(
        quizzes_v2_collection,
        sessions_collection,
    )
    return LiveQuizSessionService(repository)


def get_participant_token(
    authorization: Optional[str] = Header(default=None),
    x_participant_token: Optional[str] = Header(default=None),
) -> str:
    if x_participant_token:
        return x_participant_token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    raise HTTPException(status_code=401, detail="Participant token missing")


@router.post(
    "/quizzes/{quiz_id}/access-code",
    response_model=AccessCodeResponse,
)
async def generate_quiz_access_code(
    quiz_id: str,
    payload: AccessCodeCreateRequest,
    current_user: UserOut = Depends(get_verified_user),
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.generate_access_code(
        quiz_id=quiz_id,
        access_code_expires_at=payload.access_code_expires_at,
        creator_id=current_user.id,
        time_limit_minutes=payload.time_limit_minutes,
    )


@router.get("/quizzes/access/{code}", response_model=QuizAccessPreview)
async def validate_quiz_access_code(
    code: str,
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.validate_access_code(code)


@router.post(
    "/quizzes/access/{code}/start",
    response_model=StartLiveQuizSessionResponse,
)
async def start_live_quiz_session(
    code: str,
    payload: StartLiveQuizSessionRequest,
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.start_session(
        code=code,
        participant_name=payload.participant_name,
        participant_email=str(payload.participant_email)
        if payload.participant_email
        else None,
    )


@router.get(
    "/live-quiz-sessions/{session_id}",
    response_model=LiveQuizSessionState,
)
async def get_live_quiz_session(
    session_id: str,
    participant_token: str = Depends(get_participant_token),
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.get_session_state(session_id, participant_token)


@router.post(
    "/live-quiz-sessions/{session_id}/answers",
    response_model=SaveLiveQuizAnswerResponse,
)
async def save_live_quiz_answer(
    session_id: str,
    payload: SaveLiveQuizAnswerRequest,
    participant_token: str = Depends(get_participant_token),
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.save_answer(
        session_id=session_id,
        participant_token=participant_token,
        question_index=payload.question_index,
        selected_answer=payload.selected_answer,
        next_question_index=payload.next_question_index,
    )


@router.post(
    "/live-quiz-sessions/{session_id}/submit",
    response_model=SubmitLiveQuizSessionResponse,
)
async def submit_live_quiz_session(
    session_id: str,
    auto_submitted: bool = False,
    participant_token: str = Depends(get_participant_token),
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.submit_session(
        session_id=session_id,
        participant_token=participant_token,
        auto_submitted=auto_submitted,
    )


@router.get(
    "/quizzes/{quiz_id}/live-sessions",
    response_model=List[LiveQuizAnalyticsRow],
)
async def list_live_quiz_sessions(
    quiz_id: str,
    current_user: UserOut = Depends(get_verified_user),
    service: LiveQuizSessionService = Depends(get_live_quiz_service),
):
    return await service.list_analytics(quiz_id, current_user.id)
