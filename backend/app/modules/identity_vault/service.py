import secrets
import uuid
from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.disclosure import IDENTITY_TIER_FIELDS, DisclosureLevel, IdentityField
from app.modules.audit.service import AuditService
from app.modules.auth import security
from app.modules.auth.models import User
from app.modules.candidates.repository import CandidateRepository
from app.modules.identity_vault.exceptions import (
    CallsignGenerationExhaustedError,
    IdentityVaultNotFoundError,
    InvalidDisclosedFieldsError,
    RevealEventNotFoundError,
)
from app.modules.identity_vault.models import CandidateIdentityVault
from app.modules.identity_vault.repository import (
    IdentityRevealEventRepository,
    IdentityVaultRepository,
)
from app.modules.identity_vault.schemas import (
    IdentitySnapshot,
    RevealEventRead,
    VaultDashboardStats,
    VaultListItem,
)
from app.modules.projects.service import ProjectService
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_reveal.models import RevealRequestStatus
from app.modules.shadow_reveal.repository import ShadowRevealRequestRepository

_CALLSIGN_WORDS = [
    "Ghost", "Echo", "Shadow", "Phantom", "Nova", "Cipher", "Vector", "Pulse",
    "Atlas", "Orion", "Titan", "Falcon", "Spectre", "Sentinel", "Vanguard",
]  # fmt: skip
_MAX_CALLSIGN_ATTEMPTS = 5
_CANDIDATE_REF_PREFIX = "PH"


class IdentityVaultService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._vaults = IdentityVaultRepository(session)
        self._events = IdentityRevealEventRepository(session)
        self._candidates_repo = CandidateRepository(session)
        self._projects = ProjectService(session)
        self._audit = AuditService(session)
        self._shadow_jobs = ShadowJobRepository(session)
        self._shadow_applications = ShadowApplicationRepository(session)
        self._shadow_reveal_requests = ShadowRevealRequestRepository(session)

    async def generate_callsign(self, *, project_id: uuid.UUID) -> str:
        for _ in range(_MAX_CALLSIGN_ATTEMPTS):
            callsign = f"{secrets.choice(_CALLSIGN_WORDS)}-{secrets.randbelow(90) + 10}"
            if not await self._candidates_repo.callsign_exists_in_project(project_id, callsign):
                return callsign
        raise CallsignGenerationExhaustedError()

    async def generate_candidate_ref(self) -> str:
        result = await self._session.execute(text("SELECT nextval('candidate_ref_seq')"))
        seq = result.scalar_one()
        year = datetime.now(timezone.utc).year
        return f"{_CANDIDATE_REF_PREFIX}-{year}-{seq:04d}"

    async def create_vault_record(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        project_id: uuid.UUID,
        full_name: str,
        email: str | None,
        phone: str | None,
    ) -> CandidateIdentityVault:
        return await self._vaults.create(
            company_id=company_id,
            candidate_id=candidate_id,
            project_id=project_id,
            full_name_encrypted=security.encrypt_secret(full_name),
            email_encrypted=security.encrypt_secret(email) if email else None,
            phone_encrypted=security.encrypt_secret(phone) if phone else None,
        )

    async def _get_vault(self, candidate_id: uuid.UUID) -> CandidateIdentityVault:
        vault = await self._vaults.get_by_candidate_id(candidate_id)
        if vault is None:
            raise IdentityVaultNotFoundError()
        return vault

    async def update_vault_fields(
        self,
        *,
        candidate_id: uuid.UUID,
        location: str | None,
        current_employer: str | None,
        current_title: str | None,
        linkedin_url: str | None,
    ) -> CandidateIdentityVault:
        vault = await self._get_vault(candidate_id)
        if location is not None:
            vault.location_encrypted = security.encrypt_secret(location)
        if current_employer is not None:
            vault.current_employer_encrypted = security.encrypt_secret(current_employer)
        if current_title is not None:
            vault.current_title_encrypted = security.encrypt_secret(current_title)
        if linkedin_url is not None:
            vault.linkedin_url_encrypted = security.encrypt_secret(linkedin_url)
        await self._session.flush()
        return vault

    async def populate_from_sanitize(
        self,
        *,
        candidate_id: uuid.UUID,
        email: str | None,
        phone: str | None,
        linkedin_url: str | None,
    ) -> None:
        """Best-effort fill from resume-text extraction at sanitize time. Only ever fills fields
        that are still NULL — never overwrites a value an Owner already entered manually via the
        Vault tab (e.g. if a recruiter corrected a mis-parsed phone number by hand)."""

        vault = await self._get_vault(candidate_id)
        if vault.email_encrypted is None and email:
            vault.email_encrypted = security.encrypt_secret(email)
        if vault.phone_encrypted is None and phone:
            vault.phone_encrypted = security.encrypt_secret(phone)
        if vault.linkedin_url_encrypted is None and linkedin_url:
            vault.linkedin_url_encrypted = security.encrypt_secret(linkedin_url)
        await self._session.flush()

    async def get_decrypted_full_name(self, candidate_id: uuid.UUID) -> str:
        vault = await self._get_vault(candidate_id)
        return security.decrypt_secret(vault.full_name_encrypted)

    async def reveal_identity(
        self,
        *,
        actor: User,
        candidate_id: uuid.UUID,
        reason: str,
        ip_address: str | None,
        disclosure_level: DisclosureLevel = DisclosureLevel.FULL,
        disclosed_fields: list[IdentityField] | None = None,
    ) -> IdentitySnapshot:
        vault = await self._get_vault(candidate_id)
        candidate = await self._candidates_repo.get_by_id(candidate_id)
        if candidate is None:
            raise IdentityVaultNotFoundError()

        if disclosed_fields is not None:
            if not disclosed_fields:
                raise InvalidDisclosedFieldsError()
            effective_fields = set(disclosed_fields)
            stored_level = DisclosureLevel.CUSTOM
        else:
            effective_fields = set(IDENTITY_TIER_FIELDS[disclosure_level])
            stored_level = disclosure_level

        event = await self._events.create(
            company_id=actor.company_id,
            candidate_id=candidate_id,
            project_id=vault.project_id,
            actor_user_id=actor.id,
            reason=reason,
            ip_address=ip_address,
            disclosure_level=stored_level.value,
            disclosed_fields=[f.value for f in effective_fields],
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.identity_revealed",
            target_type="candidate",
            target_id=candidate_id,
            extra_data={
                "reveal_event_id": str(event.id),
                "reason": reason,
                "disclosure_level": stored_level.value,
            },
        )

        def _decrypt(value: str | None) -> str | None:
            return security.decrypt_secret(value) if value else None

        _T = TypeVar("_T")

        def _field(field: IdentityField, value: _T | None) -> _T | None:
            return value if field in effective_fields else None

        return IdentitySnapshot(
            reveal_event_id=event.id,
            disclosure_level=stored_level,
            disclosed_fields=sorted(effective_fields, key=lambda f: f.value),
            callsign=candidate.callsign,
            candidate_ref=candidate.candidate_ref,
            full_name=_field(
                IdentityField.FULL_NAME, security.decrypt_secret(vault.full_name_encrypted)
            ),
            email=_field(IdentityField.EMAIL, _decrypt(vault.email_encrypted)),
            phone=_field(IdentityField.PHONE, _decrypt(vault.phone_encrypted)),
            location=_field(IdentityField.LOCATION, _decrypt(vault.location_encrypted)),
            current_employer=_field(
                IdentityField.CURRENT_EMPLOYER, _decrypt(vault.current_employer_encrypted)
            ),
            current_title=_field(
                IdentityField.CURRENT_TITLE, _decrypt(vault.current_title_encrypted)
            ),
            linkedin_url=_field(IdentityField.LINKEDIN_URL, _decrypt(vault.linkedin_url_encrypted)),
            expected_salary=_field(IdentityField.EXPECTED_SALARY, candidate.expected_salary),
        )

    async def close_reveal(self, *, reveal_event_id: uuid.UUID, duration_seconds: int) -> None:
        event = await self._events.get_by_id(reveal_event_id)
        if event is None:
            raise RevealEventNotFoundError()
        await self._events.close(event, duration_seconds=duration_seconds)

    async def list_vault_for_project(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[VaultListItem]:
        await self._projects.get_project(company_id=company_id, project_id=project_id)

        candidates = await self._candidates_repo.list_by_company(
            company_id, project_id=project_id, limit=5000
        )
        vaults_by_candidate = {
            v.candidate_id: v for v in await self._vaults.list_by_project_id(project_id)
        }
        items: list[VaultListItem] = []
        for candidate in candidates:
            vault = vaults_by_candidate.get(candidate.id)
            vault_populated = vault is not None and any(
                [
                    vault.email_encrypted,
                    vault.phone_encrypted,
                    vault.location_encrypted,
                    vault.current_employer_encrypted,
                    vault.current_title_encrypted,
                    vault.linkedin_url_encrypted,
                ]
            )
            items.append(
                VaultListItem(
                    source="ats",
                    candidate_id=candidate.id,
                    callsign=candidate.callsign,
                    candidate_ref=candidate.candidate_ref,
                    status=candidate.status,
                    vault_populated=vault_populated,
                )
            )

        # This project's Shadow marketplace applicants -- a genuinely different identity system
        # (consent-gated, see shadow_reveal/__init__.py), but the same real person attached to
        # this project, and an Owner auditing "who can see what" needs to see them here too.
        # Mirrors the merge already applied to the project's Candidates tab.
        shadow_job = await self._shadow_jobs.get_by_project_id(project_id)
        if shadow_job is not None:
            applications = await self._shadow_applications.list_by_job(shadow_job.id)
            items.extend(
                VaultListItem(
                    source="shadow",
                    application_id=application.id,
                    shadow_job_id=shadow_job.id,
                    callsign=application.callsign,
                    status=application.status,
                    vault_populated=application.status == "revealed",
                )
                for application in applications
            )
        return items

    async def get_dashboard_stats(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> VaultDashboardStats:
        await self._projects.get_project(company_id=company_id, project_id=project_id)

        candidates = await self._candidates_repo.list_by_company(
            company_id, project_id=project_id, limit=5000
        )
        candidates_by_id = {c.id: c for c in candidates}
        vault_records = await self._vaults.list_by_project_id(project_id)
        events = await self._events.list_by_project_id(project_id, limit=20)

        actor_emails: dict[uuid.UUID, str] = {}
        for event in events:
            if event.actor_user_id is None or event.actor_user_id in actor_emails:
                continue
            actor = await self._session.get(User, event.actor_user_id)
            actor_emails[event.actor_user_id] = actor.email if actor else "Unknown"

        recent_reveals: list[RevealEventRead] = [
            RevealEventRead(
                id=e.id,
                source="ats",
                candidate_id=e.candidate_id,
                callsign=candidates_by_id[e.candidate_id].callsign,
                candidate_ref=candidates_by_id[e.candidate_id].candidate_ref,
                actor_email=(
                    actor_emails.get(e.actor_user_id, "Unknown") if e.actor_user_id else "Unknown"
                ),
                reason=e.reason,
                disclosure_level=DisclosureLevel(e.disclosure_level),
                disclosed_fields=e.disclosed_fields,
                revealed_at=e.created_at,
                closed_at=e.closed_at,
                duration_seconds=e.duration_seconds,
            )
            for e in events
            if e.candidate_id in candidates_by_id
        ]

        # Same ATS/Shadow merge as list_vault_for_project -- a Shadow reveal only ever becomes a
        # real disclosure event once the candidate approves; pending/declined requests aren't
        # "reveals" in the sense this dashboard tracks, so only approved ones count here.
        shadow_reveal_count = 0
        shadow_job = await self._shadow_jobs.get_by_project_id(project_id)
        shadow_applicant_count = 0
        if shadow_job is not None:
            applications = await self._shadow_applications.list_by_job(shadow_job.id)
            shadow_applicant_count = len(applications)
            applications_by_id = {a.id: a for a in applications}
            reveal_requests = await self._shadow_reveal_requests.list_by_application_ids(
                [a.id for a in applications]
            )
            for request in reveal_requests:
                if request.status != RevealRequestStatus.APPROVED.value:
                    continue
                shadow_reveal_count += 1
                application = applications_by_id.get(request.shadow_application_id)
                if application is None or request.responded_at is None:
                    continue
                recent_reveals.append(
                    RevealEventRead(
                        id=request.id,
                        source="shadow",
                        application_id=application.id,
                        shadow_job_id=shadow_job.id,
                        callsign=application.callsign,
                        actor_email=await self._actor_email(request.requested_by_user_id),
                        reason=request.reason or "Not specified",
                        disclosure_level=DisclosureLevel(request.disclosure_level or "full"),
                        disclosed_fields=request.disclosed_fields,
                        revealed_at=request.responded_at,
                    )
                )
        recent_reveals.sort(key=lambda r: r.revealed_at, reverse=True)

        return VaultDashboardStats(
            total_candidates=len(candidates) + shadow_applicant_count,
            active_vault_records=len(vault_records) + shadow_reveal_count,
            reveal_event_count=len(events) + shadow_reveal_count,
            recent_reveals=recent_reveals[:20],
        )

    async def _actor_email(self, user_id: uuid.UUID | None) -> str:
        if user_id is None:
            return "Unknown"
        actor = await self._session.get(User, user_id)
        return actor.email if actor else "Unknown"

    async def delete_by_candidate_ids(self, candidate_ids: list[uuid.UUID]) -> None:
        await self._vaults.delete_by_candidate_ids(candidate_ids)
        await self._events.delete_by_candidate_ids(candidate_ids)
