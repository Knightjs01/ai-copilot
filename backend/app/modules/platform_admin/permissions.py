class PlatformAdminPermissions:
    ADMINS_MANAGE = "admins.manage"
    COMPANIES_MANAGE = "companies.manage"
    COMPANIES_VIEW = "companies.view"
    JOBS_REVIEW = "jobs.review"
    JOBS_VIEW = "jobs.view"
    DANGER_ZONE_PURGE = "danger_zone.purge"
    AUDIT_VIEW = "audit.view"
    COMMERCIAL_MANAGE = "commercial.manage"
    COMPANIES_CREATE = "companies.create"


ALL_PLATFORM_ADMIN_PERMISSIONS: dict[str, str] = {
    PlatformAdminPermissions.ADMINS_MANAGE: "Create platform-admin accounts and assign roles",
    PlatformAdminPermissions.COMPANIES_MANAGE: (
        "Approve/reject access requests, suspend/reactivate companies, "
        "review company profiles"
    ),
    PlatformAdminPermissions.COMPANIES_VIEW: "View the companies and access-requests lists",
    PlatformAdminPermissions.JOBS_REVIEW: "Approve or reject a job submitted for Shadow review",
    PlatformAdminPermissions.JOBS_VIEW: "View the job-review queue",
    PlatformAdminPermissions.DANGER_ZONE_PURGE: "Purge all tenant data platform-wide",
    PlatformAdminPermissions.AUDIT_VIEW: "View the platform-admin activity log",
    PlatformAdminPermissions.COMMERCIAL_MANAGE: (
        "Change a company commercial plan and active-role limit override"
    ),
    PlatformAdminPermissions.COMPANIES_CREATE: (
        "Originate a brand-new company + Owner with no prior access request, and author its "
        "initial Shadow profile before activation"
    ),
}


class PlatformAdminRoleName:
    SUPER_ADMIN = "Super Admin"
    PLATFORM_ADMIN = "Platform Admin"
    REVIEWER = "Reviewer"
    SUPPORT_ADMIN = "Support Admin"
    ANALYTICS_READONLY = "Analytics"


# Unlike auth.permissions.ROLE_PERMISSIONS, this isn't a "runtime source of truth used when
# seeding" -- platform admins aren't multi-tenant (there's exactly one platform, not many
# companies each needing their own copy of a role), so these 5 roles + their grants are static,
# global data seeded once, directly in the migration that creates these tables. Kept here anyway
# as the readable source of intent; the migration keeps its own literal copy, same reasoning as
# auth.permissions's own comment about migrations being a historical record.
PLATFORM_ADMIN_ROLE_PERMISSIONS: dict[str, list[str]] = {
    PlatformAdminRoleName.SUPER_ADMIN: list(ALL_PLATFORM_ADMIN_PERMISSIONS.keys()),
    PlatformAdminRoleName.PLATFORM_ADMIN: [
        PlatformAdminPermissions.COMPANIES_MANAGE,
        PlatformAdminPermissions.COMPANIES_VIEW,
        PlatformAdminPermissions.JOBS_REVIEW,
        PlatformAdminPermissions.JOBS_VIEW,
        PlatformAdminPermissions.AUDIT_VIEW,
        PlatformAdminPermissions.COMMERCIAL_MANAGE,
    ],
    PlatformAdminRoleName.REVIEWER: [
        PlatformAdminPermissions.COMPANIES_VIEW,
        PlatformAdminPermissions.JOBS_REVIEW,
        PlatformAdminPermissions.JOBS_VIEW,
        PlatformAdminPermissions.AUDIT_VIEW,
    ],
    # Deliberately narrow -- expand once there's a real support workflow to gate (see the plan
    # this shipped under: "structure so individual permissions can be expanded later").
    PlatformAdminRoleName.SUPPORT_ADMIN: [
        PlatformAdminPermissions.COMPANIES_VIEW,
        PlatformAdminPermissions.AUDIT_VIEW,
    ],
    PlatformAdminRoleName.ANALYTICS_READONLY: [
        PlatformAdminPermissions.COMPANIES_VIEW,
        PlatformAdminPermissions.JOBS_VIEW,
        PlatformAdminPermissions.AUDIT_VIEW,
    ],
}
