from enum import StrEnum


class ProductItemRequestStatus(StrEnum):
    """
    Enumeration for the status of a product item request.

    Attributes:
        PENDING: The 'pending' status.
        APPROVED: The 'approved' status.
        REJECTED: The 'rejected' status.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
