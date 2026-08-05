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
}


class RoleName:
    OWNER = "Owner"
    ADMIN = "Admin"
    MEMBER = "Member"


# Note: this mapping is the runtime source of truth used when seeding a new company's roles.
# The Alembic migration that seeds the `permissions` table catalog keeps its own literal copy of
# the permission codes/descriptions, deliberately not importing this module — migrations are a
# historical record and shouldn't depend on code that will keep changing after they're written.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    RoleName.OWNER: list(ALL_PERMISSIONS.keys()),
    RoleName.ADMIN: [
        Permissions.USERS_VIEW,
        Permissions.USERS_INVITE,
        Permissions.USERS_CHANGE_ROLE,
        Permissions.USERS_REMOVE,
        Permissions.COMPANY_MANAGE_SETTINGS,
        Permissions.PROJECTS_CREATE,
        Permissions.PROJECTS_VIEW,
        Permissions.PROJECTS_UPDATE,
        Permissions.PROJECTS_DELETE,
    ],
    RoleName.MEMBER: [Permissions.USERS_VIEW, Permissions.PROJECTS_VIEW],
}
