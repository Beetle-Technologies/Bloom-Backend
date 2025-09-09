from enum import StrEnum


class KYCVerificationType(StrEnum):
    """
    Enumeration for the types of KYC verification methods.

    Attributes:
        MANUAL: Manual KYC verification.
        AUTOMATED: Automated KYC verification.
        HYBRID: Hybrid KYC verification.
    """

    MANUAL = "manual"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class KYCDocumentVerificationStatus(StrEnum):
    """
    Enumeration for the status of KYC document verification.

    Attributes:
        PENDING: Document verification is pending.
        IN_REVIEW: Document is in review.
        APPROVED: Document has been approved.
        REJECTED: Document has been rejected.
        EXPIRED: Document verification has expired.
    """

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class KYCVerificationQueueStatus(StrEnum):
    """
    Enumeration for the status in KYC verification queue.
    """

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
