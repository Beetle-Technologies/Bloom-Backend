from fastapi import APIRouter
from src.core.dependencies import auth_rate_limit, is_bloom_client, per_minute_rate_limit, strict_rate_limit

router = APIRouter(dependencies=[is_bloom_client])


@router.get("/pre_check", dependencies=[strict_rate_limit])
async def pre_check():
    """
    Pre check account to validate if authentication is possible
    """
    pass


@router.post("/verify_email", dependencies=[per_minute_rate_limit])
async def verify_email():
    """
    Verify user email address
    """
    pass


@router.post("/register", dependencies=[auth_rate_limit])
async def register():
    """
    Register a new user account
    """
    pass


@router.post("/login", dependencies=[auth_rate_limit])
async def login():
    """
    Login user via Oauth2 password flow
    """
    pass


@router.post("/logout", dependencies=[auth_rate_limit])
async def logout():
    """
    Logout user and invalidate refresh token
    """
    pass


@router.post("/refresh", dependencies=[auth_rate_limit])
async def refresh():
    """
    Refresh access token using refresh token
    """
    pass


@router.post("/forgot_password", dependencies=[auth_rate_limit])
async def forgot_password():
    """
    Request password reset
    """
    pass


@router.post("/reset_password", dependencies=[auth_rate_limit])
async def reset_password():
    """
    Reset user password using reset token
    """
    pass


@router.put("/change_password", dependencies=[auth_rate_limit])
async def change_password():
    """
    Change current user password
    """
    pass
