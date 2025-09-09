from enum import StrEnum


class Permission(StrEnum):
    """
    Enumeration for different types of permissions.
    """

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    UPDATE = "update"
    MANAGE = "manage"