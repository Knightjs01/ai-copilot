import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidates.repository import CandidateRepository
from app.modules.candidates.storage import FileStorage
from app.modules.hiring_blueprint.repository import HiringBlueprintRepository
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.historic_vault.repository import HistoricVaultRepository
from app.modules.identity_vault.repository import (
    IdentityRevealEventRepository,
    IdentityVaultRepository,
)
from app.modules.intelligence.repository import IntelligencePackRepository
from app.modules.prescreen_assessment.repository import PrescreenAssessmentRepository
from app.modules.privacy_gateway.repository import SanitizedProfileRepository
from app.modules.project_deletion.schemas import PurgeCertificate
from app.modules.projects.exceptions import ProjectNotFoundError
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository

_DATA_CATEGORIES_DESTROYED = [
    "Uploaded resumes",
    "Sanitized/anonymised CVs",
    "AI candidate intelligence packs",
    "Pre-screen assessments",
    "Candidate identity vault records",
    "Identity reveal audit trail",
    "Candidate records",
    "Hiring blueprint",
    "Hiring manager alignment",
]


class ProjectDeletionService:
    """Hard-delete orchestration for GDPR closure of a hiring project — distinct from
    ProjectService.delete_project's soft delete (archival, row retained). Deliberately its own
    module: this reaches into every other module's table, which none of the normal per-module
    services do, and it's a compliance-sensitive concern in its own right (same reasoning that
    gave privacy_gateway its own module in Phase 4)."""

    def __init__(self, session: AsyncSession, storage: FileStorage) -> None:
        self._project_repo = ProjectRepository(session)
        self._candidate_repo = CandidateRepository(session)
        self._sanitized_profile_repo = SanitizedProfileRepository(session)
        self._intelligence_pack_repo = IntelligencePackRepository(session)
        self._prescreen_assessment_repo = PrescreenAssessmentRepository(session)
        self._hiring_blueprint_repo = HiringBlueprintRepository(session)
        self._hiring_manager_alignment_repo = HiringManagerAlignmentRepository(session)
        self._vault_repo = IdentityVaultRepository(session)
        self._reveal_events_repo = IdentityRevealEventRepository(session)
        self._historic_vault_repo = HistoricVaultRepository(session)
        self._audit = AuditService(session)
        self._storage = storage

    async def burn_project(self, *, actor: User, project_id: uuid.UUID) -> PurgeCertificate:
        project = await self._get_project_tolerating_soft_delete(
            company_id=actor.company_id, project_id=project_id
        )

        candidates = await self._candidate_repo.list_all_by_project_id(project_id)
        candidate_ids = [c.id for c in candidates]

        # Delete files before DB rows: a dangling DB reference in a row we're about to delete
        # anyway is harmless, but an undeleted file is a real data leak. Most candidates will
        # already have no file here (Phase 4's sanitize flow clears it), this only matters for
        # candidates uploaded but never sanitized.
        for candidate in candidates:
            if candidate.resume_file_key is not None:
                await self._storage.delete(key=candidate.resume_file_key)

        await self._sanitized_profile_repo.delete_by_candidate_ids(candidate_ids)
        await self._intelligence_pack_repo.delete_by_candidate_ids(candidate_ids)
        await self._prescreen_assessment_repo.delete_by_candidate_ids(candidate_ids)
        # Vault records + reveal events before candidates — both FK to candidate_id.
        await self._vault_repo.delete_by_candidate_ids(candidate_ids)
        await self._reveal_events_repo.delete_by_candidate_ids(candidate_ids)
        await self._candidate_repo.delete_by_project_id(project_id)

        await self._hiring_blueprint_repo.delete_by_project_id(project_id)
        await self._hiring_manager_alignment_repo.delete_by_project_id(project_id)

        # Recorded before the project row is deleted so its title is available to embed —
        # audit_logs.target_id carries no FK constraint, so this entry survives the burn
        # regardless of ordering and stands as the compliance record that the erasure happened.
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.burned",
            target_type="project",
            target_id=project_id,
            extra_data={"title": project.title, "candidate_count": len(candidates)},
        )

        certificate = PurgeCertificate(
            project_title=project.title,
            candidate_count=len(candidates),
            data_categories_destroyed=_DATA_CATEGORIES_DESTROYED,
            purged_at=datetime.now(timezone.utc),
        )

        # Durable copy for the Historic Project Vault — the certificate above is otherwise only
        # ever returned once to the caller. purged_by_email is denormalized (not an actor FK) so
        # this record still reads correctly if the actor is later removed from the team.
        await self._historic_vault_repo.create(
            company_id=actor.company_id,
            project_id=project_id,
            project_title=certificate.project_title,
            candidate_count=certificate.candidate_count,
            data_categories_destroyed=certificate.data_categories_destroyed,
            purged_by_email=actor.email,
            purged_at=certificate.purged_at,
        )

        await self._project_repo.delete_by_id(project_id)

        return certificate

    async def _get_project_tolerating_soft_delete(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> Project:
        # Deliberately not ProjectService.get_project — that filters out already-archived
        # (soft-deleted) projects, but burning an archived project is exactly the normal GDPR
        # closure flow (archive when the role closes, burn later once erasure is required).
        project = await self._project_repo.get_by_id(project_id)
        if project is None or project.company_id != company_id:
            raise ProjectNotFoundError()
        return project
