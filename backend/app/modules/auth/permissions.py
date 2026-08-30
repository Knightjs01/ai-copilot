class Permissions:
    USERS_VIEW = "users.view"
    USERS_INVITE = "users.invite"
    USERS_CHANGE_ROLE = "users.change_role"
    USERS_REMOVE = "users.remove"
    COMPANY_MANAGE_SETTINGS = "company.manage_settings"
    PROJECTS_CREATE = "projects.create"
    PROJECTS_VIEW = "projects.view"
    PROJECTS_UPDATE = "projects.update"
    PROJECTS_DELETE = "projects.delete"
    CANDIDATES_CREATE = "candidates.create"
    CANDIDATES_VIEW = "candidates.view"
    CANDIDATES_UPDATE = "candidates.update"
    CANDIDATES_DELETE = "candidates.delete"
    IDENTITY_VAULT_REVEAL = "identity_vault.reveal"
    HISTORIC_VAULT_VIEW = "historic_vault.view"
    SHADOW_JOBS_CREATE = "shadow_jobs.create"
    SHADOW_JOBS_VIEW = "shadow_jobs.view"
    SHADOW_JOBS_UPDATE = "shadow_jobs.update"
    MESSAGES_VIEW = "messages.view"
    MESSAGES_SEND = "messages.send"
    INTERVIEWS_VIEW = "interviews.view"
    INTERVIEWS_SCHEDULE = "interviews.schedule"
    SHADOW_CANDIDATES_SEARCH = "shadow_candidates.search"
    HIRING_MANAGER_ALIGNMENT_SUBMIT = "hiring_manager_alignment.submit"
    TALENT_POOL_REQUEST = "talent_pool.request"
    TALENT_POOL_VIEW = "talent_pool.view"
    SHADOW_INTRODUCTION_REQUEST = "shadow_introduction.request"


ALL_PERMISSIONS: dict[str, str] = {
    Permissions.USERS_VIEW: "View company users",
    Permissions.USERS_INVITE: "Invite new users to the company",
    Permissions.USERS_CHANGE_ROLE: "Change another user's role",
    Permissions.USERS_REMOVE: "Remove a user from the company",
    Permissions.COMPANY_MANAGE_SETTINGS: "Manage company-level settings",
    Permissions.PROJECTS_CREATE: "Create hiring projects",
    Permissions.PROJECTS_VIEW: "View hiring projects",
    Permissions.PROJECTS_UPDATE: "Update hiring projects",
    Permissions.PROJECTS_DELETE: "Archive hiring projects",
    Permissions.CANDIDATES_CREATE: "Add candidates",
    Permissions.CANDIDATES_VIEW: "View candidates",
    Permissions.CANDIDATES_UPDATE: "Update candidates (including resume uploads)",
    Permissions.CANDIDATES_DELETE: "Archive candidates",
    Permissions.IDENTITY_VAULT_REVEAL: "Reveal candidate identity from the vault",
    Permissions.HISTORIC_VAULT_VIEW: "View purged project records and the company audit trail",
    Permissions.SHADOW_JOBS_CREATE: "Post jobs to the Shadow job board",
    Permissions.SHADOW_JOBS_VIEW: "View Shadow job postings and their anonymized applicants",
    Permissions.SHADOW_JOBS_UPDATE: "Edit, publish, or close Shadow job postings",
    Permissions.MESSAGES_VIEW: "View candidate/company message threads on Shadow applications",
    Permissions.MESSAGES_SEND: "Send messages to a Shadow applicant",
    Permissions.INTERVIEWS_VIEW: "View scheduled interviews for Shadow applicants",
    Permissions.INTERVIEWS_SCHEDULE: "Schedule, reschedule, or cancel interviews with a Shadow applicant",
    Permissions.SHADOW_CANDIDATES_SEARCH: "Search discoverable Shadow candidates ranked by AI match",
    Permissions.HIRING_MANAGER_ALIGNMENT_SUBMIT: "Submit hiring-manager top-requirements for a project",
    Permissions.TALENT_POOL_REQUEST: "Ask a Shadow applicant to be kept on file for future roles",
    Permissions.TALENT_POOL_VIEW: "View candidates who have granted future-role Talent Pool access",
    Permissions.SHADOW_INTRODUCTION_REQUEST: "Ask a discoverable Shadow candidate to start a conversation",
}


class RoleName:
    OWNER = "Owner"
    TA_ADMIN = "TA Admin"
    RECRUITER = "Recruiter"
    HIRING_MANAGER = "Hiring Manager"
    INTERVIEWER = "Interviewer"


# Note: this mapping is the runtime source of truth used when seeding a new company's roles.
# The Alembic migration that seeds the `permissions` table catalog keeps its own literal copy of
# the permission codes/descriptions, deliberately not importing this module — migrations are a
# historical record and shouldn't depend on code that will keep changing after they're written.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    # Owner is the only role that gets every permission automatically — this is also currently
    # the only place Owner and TA Admin diverge: IDENTITY_VAULT_REVEAL is deliberately absent from
    # TA Admin's explicit list below, since candidate identity reveal is Owner-exclusive by design.
    RoleName.OWNER: list(ALL_PERMISSIONS.keys()),
    RoleName.TA_ADMIN: [
        Permissions.USERS_VIEW,
        Permissions.USERS_INVITE,
        Permissions.USERS_CHANGE_ROLE,
        Permissions.USERS_REMOVE,
        Permissions.COMPANY_MANAGE_SETTINGS,
        Permissions.PROJECTS_CREATE,
        Permissions.PROJECTS_VIEW,
        Permissions.PROJECTS_UPDATE,
        Permissions.PROJECTS_DELETE,
        Permissions.CANDIDATES_CREATE,
        Permissions.CANDIDATES_VIEW,
        Permissions.CANDIDATES_UPDATE,
        Permissions.CANDIDATES_DELETE,
        Permissions.HISTORIC_VAULT_VIEW,
        Permissions.SHADOW_JOBS_CREATE,
        Permissions.SHADOW_JOBS_VIEW,
        Permissions.SHADOW_JOBS_UPDATE,
        Permissions.MESSAGES_VIEW,
        Permissions.MESSAGES_SEND,
        Permissions.INTERVIEWS_VIEW,
        Permissions.INTERVIEWS_SCHEDULE,
        Permissions.SHADOW_CANDIDATES_SEARCH,
        Permissions.HIRING_MANAGER_ALIGNMENT_SUBMIT,
        Permissions.TALENT_POOL_REQUEST,
        Permissions.TALENT_POOL_VIEW,
        Permissions.SHADOW_INTRODUCTION_REQUEST,
    ],
    # Recruiter is the day-to-day operational role -- real create/update rights across both the
    # ATS pipeline and the Shadow marketplace, resource-scoped to assigned projects (like the old
    # Member), but no team/company management, no project or candidate deletion, no identity
    # reveal.
    RoleName.RECRUITER: [
        Permissions.USERS_VIEW,
        Permissions.PROJECTS_VIEW,
        Permissions.CANDIDATES_CREATE,
        Permissions.CANDIDATES_VIEW,
        Permissions.CANDIDATES_UPDATE,
        Permissions.SHADOW_JOBS_CREATE,
        Permissions.SHADOW_JOBS_VIEW,
        Permissions.SHADOW_JOBS_UPDATE,
        Permissions.MESSAGES_VIEW,
        Permissions.MESSAGES_SEND,
        Permissions.INTERVIEWS_VIEW,
        Permissions.INTERVIEWS_SCHEDULE,
        Permissions.SHADOW_CANDIDATES_SEARCH,
        Permissions.TALENT_POOL_REQUEST,
        Permissions.TALENT_POOL_VIEW,
        Permissions.SHADOW_INTRODUCTION_REQUEST,
    ],
    # Resource-scoped to projects it's been added to (via ProjectMember, same mechanism Recruiter
    # uses) -- reviews candidates and submits hiring-manager alignment for its own project(s) only.
    RoleName.HIRING_MANAGER: [
        Permissions.USERS_VIEW,
        Permissions.PROJECTS_VIEW,
        Permissions.CANDIDATES_VIEW,
        Permissions.HIRING_MANAGER_ALIGNMENT_SUBMIT,
        Permissions.TALENT_POOL_VIEW,
    ],
    # Resource-scoped to specific interviews via interview_participants -- the narrowest role,
    # sees only the interview(s) it's been assigned to conduct.
    RoleName.INTERVIEWER: [
        Permissions.USERS_VIEW,
        Permissions.INTERVIEWS_VIEW,
    ],
}
