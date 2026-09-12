"""
AgentForge RBAC – Role-Based Access Control.

Defines roles and permissions. FastAPI dependency for authorization.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status

from agentforge.constants import UserRole


class Permission(str, Enum):
    """Fine-grained permissions."""
    # Projects
    CREATE_PROJECT = "create_project"
    READ_PROJECT = "read_project"
    DELETE_PROJECT = "delete_project"
    DOWNLOAD_FILES = "download_files"
    # Monitoring
    VIEW_MONITORING = "view_monitoring"
    VIEW_COSTS = "view_costs"
    # Admin
    MANAGE_USERS = "manage_users"
    VIEW_ALL_PROJECTS = "view_all_projects"
    RESET_SYSTEM = "reset_system"


# Role → Permissions mapping
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: {p for p in Permission},  # All permissions
    UserRole.USER: {
        Permission.CREATE_PROJECT,
        Permission.READ_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.DOWNLOAD_FILES,
        Permission.VIEW_MONITORING,
        Permission.VIEW_COSTS,
    },
    UserRole.VIEWER: {
        Permission.READ_PROJECT,
        Permission.DOWNLOAD_FILES,
        Permission.VIEW_MONITORING,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        user_role = UserRole(role)
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    except ValueError:
        return False


def require_permission(permission: Permission) -> Callable:
    """
    FastAPI dependency factory for permission-based authorization.

    Usage:
        @router.post("/projects", dependencies=[Depends(require_permission(Permission.CREATE_PROJECT))])
        async def create_project(...):
            ...
    """
    async def _check_permission(current_user=Depends(_get_current_user_stub)):
        if not has_permission(getattr(current_user, "role", "viewer"), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}",
            )
        return current_user

    return _check_permission


async def _get_current_user_stub():
    """Stub — replaced by api/auth.py's get_current_user in the actual app."""
    pass


def require_role(required_role: UserRole) -> Callable:
    """FastAPI dependency that requires a minimum role level."""
    role_hierarchy = {UserRole.VIEWER: 0, UserRole.USER: 1, UserRole.ADMIN: 2}

    async def _check_role(current_user=Depends(_get_current_user_stub)):
        user_role_value = role_hierarchy.get(
            UserRole(getattr(current_user, "role", "viewer")), 0
        )
        required_value = role_hierarchy.get(required_role, 0)
        if user_role_value < required_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' or higher required.",
            )
        return current_user

    return _check_role
