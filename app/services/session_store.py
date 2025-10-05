from __future__ import annotations

import time
from typing import Dict, Optional
from uuid import uuid4

from app.schemas import CoachingResponse


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, object]] = {}

    def create(self) -> str:
        session_id = uuid4().hex
        self._sessions[session_id] = {
            "created_at": time.time(),
            "last_response": None,
        }
        return session_id

    def set_last_response(self, session_id: str, response: CoachingResponse) -> None:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        self._sessions[session_id]["last_response"] = response

    def get_last_response(self, session_id: str) -> Optional[CoachingResponse]:
        data = self._sessions.get(session_id)
        if not data:
            return None
        return data.get("last_response")  # type: ignore[return-value]

    def has(self, session_id: str) -> bool:
        return session_id in self._sessions


store = SessionStore()
