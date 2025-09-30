from fastapi import APIRouter

router = APIRouter()


@router.get("/currencies")
async def get_currencies():
    """
    Get a list of supported currencies
    """
    pass


@router.get("/countries")
async def get_countries():
    """
    Get a list of supported countries
    """
    pass
