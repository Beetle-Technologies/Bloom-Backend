from enum import StrEnum


class ResaleRequestStatus(StrEnum):
    """
    Enumeration for the status of a resale request.

    Attributes:
        PENDING: The 'pending' status.
        APPROVED: The 'approved' status.
        REJECTED: The 'rejected' status.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
