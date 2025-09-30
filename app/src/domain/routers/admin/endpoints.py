from fastapi import APIRouter, status

router = APIRouter()


@router.post("/catalog/items", status_code=status.HTTP_200_OK)
async def add_to_catalog():
    """
    Add a new item from a supplier to the catalog.
    """
    pass
