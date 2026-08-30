import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.messages.models import Message, MessageThread


class MessageThreadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_shadow_application_id(
        self, shadow_application_id: uuid.UUID
    ) -> MessageThread | None:
        result = await self._session.execute(
            select(MessageThread).where(
                MessageThread.shadow_application_id == shadow_application_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_application_ids(
        self, shadow_application_ids: list[uuid.UUID]
    ) -> list[MessageThread]:
        if not shadow_application_ids:
            return []
        result = await self._session.execute(
            select(MessageThread).where(
                MessageThread.shadow_application_id.in_(shadow_application_ids)
            )
        )
        return list(result.scalars().all())

    async def list_by_company_id(self, company_id: uuid.UUID) -> list[MessageThread]:
        """Every conversation thread at this company, across every candidate -- powers the
        company-wide activity feed (candidate_activity module)."""
        result = await self._session.execute(
            select(MessageThread)
            .where(MessageThread.company_id == company_id)
            .order_by(MessageThread.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_company_and_candidate(
        self, *, company_id: uuid.UUID, candidate_user_id: uuid.UUID
    ) -> list[MessageThread]:
        """This candidate's conversation thread(s) at one company -- powers the per-candidate
        interaction timeline. In practice at most one thread per (company, candidate) pair today
        (one per application), but returned as a list since nothing enforces that at the DB
        level."""
        result = await self._session.execute(
            select(MessageThread).where(
                MessageThread.company_id == company_id,
                MessageThread.candidate_user_id == candidate_user_id,
            )
        )
        return list(result.scalars().all())

    async def list_by_candidate_user_id(self, candidate_user_id: uuid.UUID) -> list[MessageThread]:
        result = await self._session.execute(
            select(MessageThread).where(MessageThread.candidate_user_id == candidate_user_id)
        )
        return list(result.scalars().all())

    async def get_or_create_for_application(
        self,
        *,
        shadow_application_id: uuid.UUID,
        company_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
    ) -> MessageThread:
        existing = await self.get_by_shadow_application_id(shadow_application_id)
        if existing is not None:
            return existing
        thread = MessageThread(
            shadow_application_id=shadow_application_id,
            company_id=company_id,
            candidate_user_id=candidate_user_id,
        )
        self._session.add(thread)
        await self._session.flush()
        return thread

    async def mark_candidate_read(self, thread: MessageThread) -> MessageThread:
        thread.candidate_last_read_at = datetime.now(timezone.utc)
        await self._session.flush()
        return thread

    async def mark_company_read(self, thread: MessageThread) -> MessageThread:
        thread.company_last_read_at = datetime.now(timezone.utc)
        await self._session.flush()
        return thread

    async def delete_by_shadow_application_ids(
        self, shadow_application_ids: list[uuid.UUID]
    ) -> None:
        if not shadow_application_ids:
            return
        await self._session.execute(
            delete(MessageThread).where(
                MessageThread.shadow_application_id.in_(shadow_application_ids)
            )
        )


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        thread_id: uuid.UUID,
        sender_type: str,
        sender_user_id: uuid.UUID | None,
        sender_candidate_user_id: uuid.UUID | None,
        body: str,
    ) -> Message:
        message = Message(
            thread_id=thread_id,
            sender_type=sender_type,
            sender_user_id=sender_user_id,
            sender_candidate_user_id=sender_candidate_user_id,
            body=body,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_by_thread_id(self, thread_id: uuid.UUID) -> list[Message]:
        result = await self._session.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def list_by_thread_ids(self, thread_ids: list[uuid.UUID]) -> list[Message]:
        """Every message (both senders) across the given threads, in one call -- used for
        building the candidate's own inbox summaries (last message + unread) without N+1."""
        if not thread_ids:
            return []
        result = await self._session.execute(
            select(Message).where(Message.thread_id.in_(thread_ids))
        )
        return list(result.scalars().all())

    async def list_candidate_messages_for_threads(
        self, thread_ids: list[uuid.UUID]
    ) -> list[Message]:
        """Only candidate-sent messages across the given threads, in one call -- used for the
        company-side bulk unread-count lookup (ShadowJobService.list_applicants)."""
        if not thread_ids:
            return []
        result = await self._session.execute(
            select(Message).where(
                Message.thread_id.in_(thread_ids), Message.sender_type == "candidate"
            )
        )
        return list(result.scalars().all())
