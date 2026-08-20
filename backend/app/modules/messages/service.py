import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.messages.exceptions import ApplicationNotFoundError
from app.modules.messages.models import Message, MessageThread
from app.modules.messages.repository import MessageRepository, MessageThreadRepository
from app.modules.messages.schemas import MessageRead, MessageThreadRead, MessageThreadSummary
from app.modules.shadow_jobs.models import ShadowApplication
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._threads = MessageThreadRepository(session)
        self._messages = MessageRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._audit = AuditService(session)

    # --- Candidate side ----------------------------------------------------------------------

    async def send_as_candidate(
        self, *, candidate: CandidateUser, application_id: uuid.UUID, body: str
    ) -> MessageThreadRead:
        application = await self._get_candidate_application(
            candidate=candidate, application_id=application_id
        )
        thread = await self._threads.get_or_create_for_application(
            shadow_application_id=application.id,
            company_id=application.company_id,
            candidate_user_id=candidate.id,
        )
        await self._messages.create(
            thread_id=thread.id,
            sender_type="candidate",
            sender_user_id=None,
            sender_candidate_user_id=candidate.id,
            body=body,
        )
        await self._threads.mark_candidate_read(thread)
        await self._audit.record(
            company_id=application.company_id,
            actor_user_id=None,
            action="message.sent",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"sender_type": "candidate"},
        )
        return await self._build_thread_read(
            thread=thread, application=application, viewer_is_candidate=True
        )

    async def get_thread_for_candidate(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> MessageThreadRead:
        application = await self._get_candidate_application(
            candidate=candidate, application_id=application_id
        )
        thread = await self._threads.get_by_shadow_application_id(application.id)
        if thread is None:
            return MessageThreadRead(application_id=application.id, messages=[])
        await self._threads.mark_candidate_read(thread)
        return await self._build_thread_read(
            thread=thread, application=application, viewer_is_candidate=True
        )

    async def list_threads_for_candidate(
        self, *, candidate: CandidateUser
    ) -> list[MessageThreadSummary]:
        threads = await self._threads.list_by_candidate_user_id(candidate.id)
        if not threads:
            return []

        thread_ids = [t.id for t in threads]
        all_messages = await self._messages.list_by_thread_ids(thread_ids)
        by_thread: dict[uuid.UUID, list[Message]] = defaultdict(list)
        for message in all_messages:
            by_thread[message.thread_id].append(message)

        summaries: list[MessageThreadSummary] = []
        for thread in threads:
            application = await self._applications.get_by_id(thread.shadow_application_id)
            if application is None:
                continue
            job = await self._jobs.get_by_id(application.shadow_job_id)
            company = await self._session.get(Company, thread.company_id)
            msgs = sorted(by_thread.get(thread.id, []), key=lambda m: m.created_at)
            last = msgs[-1] if msgs else None
            cutoff = thread.candidate_last_read_at
            unread = sum(
                1
                for m in msgs
                if m.sender_type == "company" and (cutoff is None or m.created_at > cutoff)
            )
            summaries.append(
                MessageThreadSummary(
                    application_id=application.id,
                    job_title=job.title if job else "Unknown role",
                    company_name=company.name if company else "Unknown company",
                    callsign=application.callsign,
                    last_message_preview=last.body[:140] if last else None,
                    last_message_at=last.created_at if last else thread.created_at,
                    unread_count=unread,
                )
            )
        summaries.sort(
            key=lambda s: s.last_message_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return summaries

    # --- Company side --------------------------------------------------------------------------

    async def send_as_company(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, body: str
    ) -> MessageThreadRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        thread = await self._threads.get_or_create_for_application(
            shadow_application_id=application.id,
            company_id=actor.company_id,
            candidate_user_id=application.candidate_user_id,
        )
        await self._messages.create(
            thread_id=thread.id,
            sender_type="company",
            sender_user_id=actor.id,
            sender_candidate_user_id=None,
            body=body,
        )
        await self._threads.mark_company_read(thread)
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="message.sent",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"sender_type": "company"},
        )
        return await self._build_thread_read(
            thread=thread, application=application, viewer_is_candidate=False
        )

    async def get_thread_for_company(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> MessageThreadRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        thread = await self._threads.get_by_shadow_application_id(application.id)
        if thread is None:
            return MessageThreadRead(application_id=application.id, messages=[])
        await self._threads.mark_company_read(thread)
        return await self._build_thread_read(
            thread=thread, application=application, viewer_is_candidate=False
        )

    async def unread_counts_for_applications(
        self, *, application_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Bulk lookup used by ShadowJobService.list_applicants to populate
        ShadowProfile.unread_message_count without a per-applicant round trip."""
        if not application_ids:
            return {}
        threads = await self._threads.list_by_application_ids(application_ids)
        thread_by_app = {t.shadow_application_id: t for t in threads}
        thread_ids = [t.id for t in threads]
        candidate_messages = await self._messages.list_candidate_messages_for_threads(thread_ids)
        by_thread: dict[uuid.UUID, list[Message]] = defaultdict(list)
        for message in candidate_messages:
            by_thread[message.thread_id].append(message)

        counts: dict[uuid.UUID, int] = {}
        for app_id in application_ids:
            thread = thread_by_app.get(app_id)
            if thread is None:
                counts[app_id] = 0
                continue
            cutoff = thread.company_last_read_at
            counts[app_id] = sum(
                1 for m in by_thread.get(thread.id, []) if cutoff is None or m.created_at > cutoff
            )
        return counts

    # --- Shared helpers ------------------------------------------------------------------------

    async def _get_candidate_application(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> ShadowApplication:
        application = await self._applications.get_by_id(application_id)
        if application is None or application.candidate_user_id != candidate.id:
            raise ApplicationNotFoundError()
        return application

    async def _get_company_application(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowApplication:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != company_id or job.deleted_at is not None:
            raise ApplicationNotFoundError()
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ApplicationNotFoundError()
        return application

    async def _build_thread_read(
        self, *, thread: MessageThread, application: ShadowApplication, viewer_is_candidate: bool
    ) -> MessageThreadRead:
        messages = await self._messages.list_by_thread_id(thread.id)
        company = await self._session.get(Company, application.company_id)
        company_name = company.name if company else "Unknown company"
        reads = [
            MessageRead(
                id=m.id,
                sender_type=m.sender_type,  # type: ignore[arg-type]
                sender_label=application.callsign if m.sender_type == "candidate" else company_name,
                body=m.body,
                created_at=m.created_at,
                is_mine=(m.sender_type == "candidate") == viewer_is_candidate,
            )
            for m in messages
        ]
        return MessageThreadRead(application_id=application.id, messages=reads)
