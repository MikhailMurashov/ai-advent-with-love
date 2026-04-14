from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    InvariantsModel,
    LongTermMemoryModel,
    MessageModel,
    PersonalizationModel,
    SessionModel,
    UserModel,
    WorkingMemoryModel,
)
from app.interfaces.repositories import Message, SessionInfo, User


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SQLiteUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, username: str) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = UserModel(id=str(uuid.uuid4()), username=username, created_at=_now())
            self._session.add(user)
            await self._session.commit()
            await self._session.refresh(user)
        return User(id=user.id, username=user.username, created_at=user.created_at)


class SQLiteSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, session_id: str) -> SessionInfo | None:
        result = await self._session.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        row = result.scalar_one_or_none()
        return self._to_info(row) if row else None

    async def create(
        self,
        user_id: str,
        model_key: str,
        strategy_type: str = "sliding_window_summary",
        system_prompt: str = "",
        title: str = "Новая сессия",
        session_id: str | None = None,
    ) -> SessionInfo:
        now = _now()
        row = SessionModel(
            id=session_id or str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            strategy_type=strategy_type,
            model_key=model_key,
            system_prompt=system_prompt,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_info(row)

    async def list_by_user(self, user_id: str) -> list[SessionInfo]:
        result = await self._session.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.updated_at.desc())
        )
        return [self._to_info(r) for r in result.scalars()]

    async def delete(self, session_id: str) -> None:
        await self._session.execute(
            delete(SessionModel).where(SessionModel.id == session_id)
        )
        await self._session.commit()

    async def save_message(self, msg: Message) -> None:
        row = MessageModel(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            tokens_prompt=msg.tokens_prompt,
            tokens_completion=msg.tokens_completion,
            elapsed_s=msg.elapsed_s,
            created_at=msg.created_at,
        )
        self._session.add(row)
        await self._session.commit()

    async def get_messages(self, session_id: str) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at)
        )
        return [
            Message(
                id=r.id,
                session_id=r.session_id,
                role=r.role,
                content=r.content or "",
                tool_calls=r.tool_calls,
                tokens_prompt=r.tokens_prompt,
                tokens_completion=r.tokens_completion,
                elapsed_s=r.elapsed_s,
                created_at=r.created_at,
            )
            for r in result.scalars()
        ]

    async def update_timestamp(self, session_id: str) -> None:
        await self._session.execute(
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(updated_at=_now())
        )
        await self._session.commit()

    def _to_info(self, row: SessionModel) -> SessionInfo:
        return SessionInfo(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            strategy_type=row.strategy_type,
            model_key=row.model_key,
            system_prompt=row.system_prompt,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SQLiteMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_working(self, session_id: str) -> dict[str, str]:
        result = await self._session.execute(
            select(WorkingMemoryModel).where(WorkingMemoryModel.session_id == session_id)
        )
        return {r.key: r.value for r in result.scalars()}

    async def set_working(self, session_id: str, key: str, value: str) -> None:
        result = await self._session.execute(
            select(WorkingMemoryModel).where(
                WorkingMemoryModel.session_id == session_id,
                WorkingMemoryModel.key == key,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = WorkingMemoryModel(
                id=str(uuid.uuid4()),
                session_id=session_id,
                key=key,
                value=value,
                created_at=_now(),
            )
            self._session.add(row)
        else:
            row.value = value
        await self._session.commit()

    async def get_long_term(self, user_id: str) -> dict[str, str]:
        result = await self._session.execute(
            select(LongTermMemoryModel).where(LongTermMemoryModel.user_id == user_id)
        )
        return {r.key: r.value for r in result.scalars()}

    async def set_long_term(self, user_id: str, key: str, value: str) -> None:
        result = await self._session.execute(
            select(LongTermMemoryModel).where(
                LongTermMemoryModel.user_id == user_id,
                LongTermMemoryModel.key == key,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = LongTermMemoryModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                key=key,
                value=value,
                created_at=_now(),
            )
            self._session.add(row)
        else:
            row.value = value
        await self._session.commit()

    async def get_personalization(self, user_id: str) -> str:
        result = await self._session.execute(
            select(PersonalizationModel).where(PersonalizationModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return row.content if row else ""

    async def set_personalization(self, user_id: str, content: str) -> None:
        result = await self._session.execute(
            select(PersonalizationModel).where(PersonalizationModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = PersonalizationModel(user_id=user_id, content=content, updated_at=_now())
            self._session.add(row)
        else:
            row.content = content
            row.updated_at = _now()
        await self._session.commit()

    async def get_invariants(self, user_id: str) -> list[str]:
        result = await self._session.execute(
            select(InvariantsModel).where(InvariantsModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return json.loads(row.rules_json) if row else []

    async def set_invariants(self, user_id: str, rules: list[str]) -> None:
        result = await self._session.execute(
            select(InvariantsModel).where(InvariantsModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = InvariantsModel(
                user_id=user_id,
                rules_json=json.dumps(rules, ensure_ascii=False),
                updated_at=_now(),
            )
            self._session.add(row)
        else:
            row.rules_json = json.dumps(rules, ensure_ascii=False)
            row.updated_at = _now()
        await self._session.commit()
