from enum import Enum
from typing import List
from fastapi import Header, HTTPException, status

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DRILLING_ENGINEER = "DRILLING_ENGINEER"
    GEOLOGIST = "GEOLOGIST"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"

ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["read", "write", "review", "admin", "train", "benchmark"],
    UserRole.DRILLING_ENGINEER: ["read", "write", "train", "benchmark"],
    UserRole.GEOLOGIST: ["read", "write"],
    UserRole.REVIEWER: ["read", "review"],
    UserRole.VIEWER: ["read"]
}

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, x_user_role: str = Header(default="ADMIN")):
        try:
            role = UserRole(x_user_role.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid user role: {x_user_role}"
            )
        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role.value} lacks required permission"
            )
        return role

require_admin = RoleChecker([UserRole.ADMIN])
require_reviewer = RoleChecker([UserRole.ADMIN, UserRole.REVIEWER])
require_engineer = RoleChecker([UserRole.ADMIN, UserRole.DRILLING_ENGINEER])
require_read = RoleChecker([UserRole.ADMIN, UserRole.DRILLING_ENGINEER, UserRole.GEOLOGIST, UserRole.REVIEWER, UserRole.VIEWER])
