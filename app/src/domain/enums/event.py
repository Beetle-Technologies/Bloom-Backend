from enum import StrEnum


class EventStatus(StrEnum):
    """
    Enumeration for the status of events in the outbox.

    Attributes:
        PENDING: Event is pending.
        PROCESSING: Event is being processed.
        PROCESSED: Event has been processed.
        FAILED: Event has failed.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
