"""
auth/rbac.py
Role-Based Access Control definitions for AppAI Hub.

Defines the 5 platform roles and a permissions helper class that gates
what each role can see or do — including the critical code-confidentiality
rule that prevents source code from being surfaced to non-developer roles.
"""

from enum import Enum


class Role(str, Enum):
    """Platform roles in ascending privilege order."""
    SUPER_ADMIN = "super_admin"
    APP_ADMIN = "app_admin"
    DEVELOPER = "developer"
    SUPPORT_AGENT = "support_agent"
    APP_USER = "app_user"


class RolePermissions:
    """
    Static permission checks keyed on Role values.

    All methods accept a Role enum member (or its string value) and return bool.
    """

    # Roles that are allowed to see raw source-code knowledge base chunks.
    _CODE_ROLES = {Role.DEVELOPER, Role.SUPER_ADMIN}

    # Roles that can register/delete/update apps.
    _MANAGE_APP_ROLES = {Role.SUPER_ADMIN, Role.APP_ADMIN}

    # Roles that can create/update/deactivate user accounts.
    _MANAGE_USER_ROLES = {Role.SUPER_ADMIN, Role.APP_ADMIN}

    # Roles that can view support tickets.
    _TICKET_ROLES = {Role.SUPER_ADMIN, Role.APP_ADMIN, Role.SUPPORT_AGENT}

    # Roles that can add documents to the knowledge base.
    _KB_WRITE_ROLES = {Role.SUPER_ADMIN, Role.APP_ADMIN, Role.DEVELOPER, Role.SUPPORT_AGENT}

    @staticmethod
    def _to_role(role) -> Role:
        """Coerce string to Role enum if needed."""
        if isinstance(role, Role):
            return role
        return Role(role)

    @staticmethod
    def can_see_source_code(role) -> bool:
        """
        Returns True only for DEVELOPER and SUPER_ADMIN.
        This gate is the backbone of code-confidentiality enforcement:
        the LLM router and KB retriever both check this before exposing
        source-code chunks.
        """
        return RolePermissions._to_role(role) in RolePermissions._CODE_ROLES

    @staticmethod
    def can_manage_apps(role) -> bool:
        """Returns True for SUPER_ADMIN and APP_ADMIN."""
        return RolePermissions._to_role(role) in RolePermissions._MANAGE_APP_ROLES

    @staticmethod
    def can_manage_users(role) -> bool:
        """Returns True for SUPER_ADMIN and APP_ADMIN."""
        return RolePermissions._to_role(role) in RolePermissions._MANAGE_USER_ROLES

    @staticmethod
    def can_view_tickets(role) -> bool:
        """Returns True for SUPER_ADMIN, APP_ADMIN, and SUPPORT_AGENT."""
        return RolePermissions._to_role(role) in RolePermissions._TICKET_ROLES

    @staticmethod
    def can_add_kb_docs(role) -> bool:
        """Returns True for all roles except APP_USER."""
        return RolePermissions._to_role(role) in RolePermissions._KB_WRITE_ROLES

    @staticmethod
    def get_system_prompt_role(role) -> str:
        """
        Maps a platform Role to the LLM system-prompt profile.

        Returns:
            'developer' — full technical responses, source code exposure allowed.
            'user'      — strict no-code-exposure rules apply.
        """
        r = RolePermissions._to_role(role)
        if r in RolePermissions._CODE_ROLES:
            return "developer"
        return "user"
