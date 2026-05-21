from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
import string
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from server.app.quiz.utils.grading import grade_answers
from server.app.quiz.repositories.live_session_repository import (
    LiveQuizSessionRepository,
)


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class LiveQuizSessionService:
    def __init__(self, repository: LiveQuizSessionRepository):
        self.repository = repository

    async def generate_access_code(
        self,
        quiz_id: str,
        access_code_expires_at: datetime,
        creator_id: str,
        time_limit_minutes: int,
    ) -> Dict[str, Any]:
        if _as_utc(access_code_expires_at) <= _utc_now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access code expiration must be in the future",
            )

        quiz = await self.repository.get_quiz_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        owner_id = quiz.get("owner_user_id") or quiz.get("created_by") or quiz.get("owner_id")
        if owner_id and owner_id != creator_id:
            raise HTTPException(status_code=403, detail="Not allowed")

        code = await self._generate_unique_code()
        updated_quiz = await self.repository.enable_live_quiz(
            quiz_id=quiz_id,
            access_code=code,
            time_limit_minutes=time_limit_minutes,
            access_code_expires_at=_as_utc(access_code_expires_at),
            creator_id=creator_id,
        )
        if not updated_quiz:
            raise HTTPException(status_code=500, detail="Could not enable live quiz")

        return {
            "quiz_id": str(updated_quiz["_id"]),
            "access_code": code,
            "live_quiz_enabled": True,
            "time_limit_minutes": time_limit_minutes,
            "access_code_expires_at": _as_utc(updated_quiz["access_code_expires_at"]),
        }

    async def validate_access_code(self, code: str) -> Dict[str, Any]:
        quiz = await self._get_startable_quiz(code)
        questions = quiz.get("questions") or []
        return {
            "quiz_id": str(quiz["_id"]),
            "title": quiz.get("title", "Live Quiz"),
            "total_questions": len(questions),
            "time_limit_minutes": quiz["time_limit_minutes"],
            "access_code_expires_at": _as_utc(quiz["access_code_expires_at"]),
        }

    async def start_session(
        self,
        code: str,
        participant_name: str,
        participant_email: Optional[str],
    ) -> Dict[str, Any]:
        quiz = await self._get_startable_quiz(code)
        questions = quiz.get("questions") or []
        if not questions:
            raise HTTPException(status_code=400, detail="Quiz has no questions")

        participant_token = secrets.token_urlsafe(32)
        started_at = _utc_now()
        time_limit_minutes = int(quiz["time_limit_minutes"])
        duration_seconds = time_limit_minutes * 60
        expires_at = started_at + timedelta(minutes=time_limit_minutes)
        server_now = started_at
        guest_id = f"guest_{secrets.token_urlsafe(12)}"
        session_data = {
            "quiz_id": str(quiz["_id"]),
            "participant_type": "guest",
            "user_id": None,
            "participant_name": participant_name.strip(),
            "participant_email": participant_email,
            "guest_id": guest_id,
            "participant_token_hash": _hash_token(participant_token),
            "started_at": started_at,
            "expires_at": expires_at,
            "submitted_at": None,
            "status": "active",
            "current_question_index": 0,
            "answers": [],
            "score": None,
            "total_questions": len(questions),
            "duration_seconds": duration_seconds,
            "percentage": None,
            "auto_submitted": False,
            "created_at": started_at,
            "updated_at": started_at,
        }
        session_id = await self.repository.create_session(session_data)
        remaining_seconds = self._remaining_seconds(expires_at, server_now)
        logger.info(
            {
                "event": "live_quiz_session_started",
                "session_id": session_id,
                "started_at": started_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "server_now": server_now.isoformat(),
                "time_limit_minutes": time_limit_minutes,
                "remaining_seconds": remaining_seconds,
            }
        )
        return {
            "session_id": session_id,
            "participant_token": participant_token,
            "started_at": started_at,
            "expires_at": expires_at,
            "server_now": server_now,
            "time_limit_minutes": time_limit_minutes,
            "duration_seconds": duration_seconds,
            "remaining_seconds": remaining_seconds,
            "redirect_url": f"/live-quiz/{session_id}",
        }

    async def get_session_state(
        self,
        session_id: str,
        participant_token: str,
    ) -> Dict[str, Any]:
        session = await self._get_authorized_session(session_id, participant_token)
        quiz = await self.repository.get_quiz_by_id(session["quiz_id"])
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        if self._is_expired(session) and session.get("status") == "active":
            session = await self._finalize_session(
                session,
                quiz,
                auto_submitted=True,
            )

        return self._build_session_state(session, quiz)

    async def save_answer(
        self,
        session_id: str,
        participant_token: str,
        question_index: int,
        selected_answer: str,
        next_question_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        session = await self._get_authorized_session(session_id, participant_token)
        if session.get("status") != "active":
            raise HTTPException(status_code=409, detail="Session is not active")
        if self._is_expired(session):
            quiz = await self.repository.get_quiz_by_id(session["quiz_id"])
            if quiz:
                await self._finalize_session(session, quiz, auto_submitted=True)
            raise HTTPException(status_code=409, detail="Session has expired")
        if question_index < 0 or question_index >= session["total_questions"]:
            raise HTTPException(status_code=400, detail="Invalid question index")

        next_index = (
            next_question_index
            if next_question_index is not None
            else session["current_question_index"]
        )
        if next_index < 0 or next_index >= session["total_questions"]:
            raise HTTPException(status_code=400, detail="Invalid next question index")
        updated = await self.repository.save_answer(
            session_id,
            question_index,
            selected_answer,
            next_index,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "status": updated["status"],
            "current_question_index": updated["current_question_index"],
            "remaining_seconds": self._remaining_seconds(updated["expires_at"]),
        }

    async def submit_session(
        self,
        session_id: str,
        participant_token: str,
        auto_submitted: bool = False,
    ) -> Dict[str, Any]:
        session = await self._get_authorized_session(session_id, participant_token)
        quiz = await self.repository.get_quiz_by_id(session["quiz_id"])
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        if session.get("status") == "submitted":
            return self._submission_response(session, already_submitted=True)

        is_expired = self._is_expired(session)
        if auto_submitted and not is_expired:
            logger.info(
                {
                    "event": "live_quiz_auto_submit_rejected_before_expiry",
                    "session_id": session_id,
                    "server_now": _utc_now().isoformat(),
                    "expires_at": _as_utc(session["expires_at"]).isoformat(),
                    "remaining_seconds": self._remaining_seconds(session["expires_at"]),
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session has not expired",
            )

        finalized = await self._finalize_session(
            session,
            quiz,
            auto_submitted=auto_submitted or is_expired,
        )
        return self._submission_response(finalized)

    async def list_analytics(self, quiz_id: str, requester_id: str) -> List[Dict[str, Any]]:
        quiz = await self.repository.get_quiz_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        owner_id = quiz.get("created_by") or quiz.get("owner_id")
        if owner_id and owner_id != requester_id:
            raise HTTPException(status_code=403, detail="Not allowed")

        sessions = await self.repository.list_quiz_sessions(quiz_id)
        return [self._analytics_row(session) for session in sessions]

    async def _generate_unique_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(20):
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if not await self.repository.access_code_exists(code):
                return code
        raise HTTPException(status_code=500, detail="Could not generate access code")

    async def _get_startable_quiz(self, code: str) -> Dict[str, Any]:
        quiz = await self.repository.get_quiz_by_access_code(code)
        if not quiz or not quiz.get("live_quiz_enabled"):
            raise HTTPException(status_code=404, detail="Live quiz not found")

        expires_at = quiz.get("access_code_expires_at")
        if not expires_at or _as_utc(expires_at) <= _utc_now():
            raise HTTPException(status_code=410, detail="Access code has expired")
        if not quiz.get("time_limit_minutes"):
            raise HTTPException(status_code=400, detail="Quiz time limit is not configured")
        return quiz

    async def _get_authorized_session(
        self,
        session_id: str,
        participant_token: str,
    ) -> Dict[str, Any]:
        if not participant_token:
            raise HTTPException(status_code=401, detail="Participant token missing")
        session = await self.repository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("participant_token_hash") != _hash_token(participant_token):
            raise HTTPException(status_code=403, detail="Invalid participant token")
        return session

    async def _finalize_session(
        self,
        session: Dict[str, Any],
        quiz: Dict[str, Any],
        auto_submitted: bool,
    ) -> Dict[str, Any]:
        graded = self._grade_session(session, quiz)
        submitted_at = _utc_now()
        updated = await self.repository.update_session(
            str(session["_id"]),
            {
                "status": "submitted",
                "submitted_at": submitted_at,
                "score": graded["score"],
                "percentage": graded["percentage"],
                "auto_submitted": auto_submitted,
            },
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        return updated

    def _grade_session(
        self,
        session: Dict[str, Any],
        quiz: Dict[str, Any],
    ) -> Dict[str, Any]:
        questions = quiz.get("questions") or []
        answer_by_index = {
            answer["question_index"]: answer.get("selected_answer", "")
            for answer in session.get("answers", [])
        }
        grading_payload = []
        for index, question in enumerate(questions):
            correct_answer = question.get("correct_answer") or question.get("answer")
            grading_payload.append(
                {
                    "question": question.get("question", ""),
                    "user_answer": answer_by_index.get(index, ""),
                    "correct_answer": correct_answer,
                    "question_type": question.get("question_type")
                    or quiz.get("quiz_type")
                    or "multichoice",
                    "source": question.get("source", "live"),
                }
            )

        graded_answers = grade_answers(grading_payload, "mock")
        score = sum(1 for answer in graded_answers if answer.get("is_correct"))
        total = len(questions)
        percentage = round((score / total) * 100, 2) if total else 0
        return {"score": score, "percentage": percentage}

    def _build_session_state(
        self,
        session: Dict[str, Any],
        quiz: Dict[str, Any],
    ) -> Dict[str, Any]:
        current_index = session.get("current_question_index", 0)
        questions = quiz.get("questions") or []
        question = None
        if session.get("status") == "active" and 0 <= current_index < len(questions):
            raw_question = questions[current_index]
            question = self._public_question(
                raw_question,
                current_index,
                session.get("answers", []),
                quiz.get("quiz_type"),
            )

        server_now = _utc_now()
        time_limit_minutes = int(quiz["time_limit_minutes"])
        duration_seconds = session.get("duration_seconds") or time_limit_minutes * 60
        started_at = _as_utc(session["started_at"])
        expires_at = _as_utc(session["expires_at"])
        submitted_at = (
            _as_utc(session["submitted_at"]) if session.get("submitted_at") else None
        )

        return {
            "session_id": str(session["_id"]),
            "quiz_id": session["quiz_id"],
            "title": quiz.get("title", "Live Quiz"),
            "participant_name": session["participant_name"],
            "participant_email": session.get("participant_email"),
            "started_at": started_at,
            "expires_at": expires_at,
            "server_now": server_now,
            "submitted_at": submitted_at,
            "status": session["status"],
            "current_question_index": current_index,
            "total_questions": session["total_questions"],
            "time_limit_minutes": time_limit_minutes,
            "duration_seconds": duration_seconds,
            "remaining_seconds": self._remaining_seconds(expires_at, server_now),
            "question": question,
            "answers": session.get("answers", []),
            "score": session.get("score"),
            "percentage": session.get("percentage"),
            "auto_submitted": session.get("auto_submitted", False),
        }

    def _public_question(
        self,
        question: Dict[str, Any],
        index: int,
        answers: List[Dict[str, Any]],
        quiz_type: Optional[str],
    ) -> Dict[str, Any]:
        selected_answer = None
        for answer in answers:
            if answer.get("question_index") == index:
                selected_answer = answer.get("selected_answer")
                break
        return {
            "question_index": index,
            "question": question.get("question", ""),
            "options": question.get("options"),
            "question_type": question.get("question_type") or quiz_type,
            "selected_answer": selected_answer,
        }

    def _submission_response(
        self,
        session: Dict[str, Any],
        already_submitted: bool = False,
    ) -> Dict[str, Any]:
        return {
            "status": "already_submitted" if already_submitted else "submitted",
            "score": session["score"],
            "total_questions": session["total_questions"],
            "percentage": session["percentage"],
            "submitted_at": _as_utc(session["submitted_at"]),
            "auto_submitted": session.get("auto_submitted", False),
        }

    def _analytics_row(self, session: Dict[str, Any]) -> Dict[str, Any]:
        duration_seconds = None
        if session.get("submitted_at") and session.get("started_at"):
            duration_seconds = int(
                (_as_utc(session["submitted_at"]) - _as_utc(session["started_at"])).total_seconds()
            )
        return {
            "session_id": str(session["_id"]),
            "participant_name": session.get("participant_name", ""),
            "participant_email": session.get("participant_email"),
            "score": session.get("score"),
            "total_questions": session.get("total_questions", 0),
            "percentage": session.get("percentage"),
            "submitted_at": session.get("submitted_at"),
            "duration_seconds": duration_seconds,
            "status": session.get("status", "active"),
            "auto_submitted": session.get("auto_submitted", False),
        }

    def _is_expired(self, session: Dict[str, Any]) -> bool:
        return _as_utc(session["expires_at"]) <= _utc_now()

    def _remaining_seconds(
        self,
        expires_at: datetime,
        server_now: Optional[datetime] = None,
    ) -> int:
        now = _as_utc(server_now) if server_now else _utc_now()
        return max(0, int((_as_utc(expires_at) - now).total_seconds()))
