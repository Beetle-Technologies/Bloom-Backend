from enum import StrEnum


class PaginationType(StrEnum):
    """
    Enumeration for pagination types

    Attributes:\n
        KEYSET: Keyset pagination, also known as cursor-based pagination.
        OFFSET: Offset pagination, also known as page-based pagination.
    """

    KEYSET = "keyset"
    OFFSET = "offset"


class SortDirection(StrEnum):
    """
    Enumeration for sort directions

    Attributes:\n
        ASC: Ascending order.
        DESC: Descending order.
    """

    ASC = "asc"
    DESC = "desc"
