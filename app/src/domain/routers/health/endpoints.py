from fastapi import APIRouter

router = APIRouter()


@router.get("/", include_in_schema=False)
def health_check() -> dict[str, str]:
    """
    Basic health check endpoint to verify the bloom is running.
    """
    return {"status": "healthy"}
