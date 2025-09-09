from fastapi import APIRouter
from src.core.dependencies import api_rate_limit, is_bloom_client

router = APIRouter(dependencies=[is_bloom_client])


@router.get("/me", dependencies=[api_rate_limit])
async def me():
    """
    Get current user information
    """
    pass


@router.put("/me", dependencies=[api_rate_limit])
async def update_me():
    """
    Update current user information
    """
    pass


@router.delete("/me", dependencies=[api_rate_limit])
async def delete_me():
    """
    Delete current user account
    """
    pass


@router.get("/me/preferences", dependencies=[api_rate_limit])
async def get_preferences():
    """
    Get current user preferences
    """
    pass


@router.put("/me/preferences", dependencies=[api_rate_limit])
async def update_preferences():
    """
    Update current user preferences
    """
    pass


@router.get("/me/notifications", dependencies=[api_rate_limit])
async def get_notifications():
    """
    Get current user notifications
    """
    pass
