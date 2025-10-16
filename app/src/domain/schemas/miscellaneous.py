from pydantic import BaseModel, Field


class GenerateGIDRequest(BaseModel):
    """
    Schema for the request body to generate a new GID.
    """

    resource_type: str = Field(
        ..., description="The resource type for the GID (e.g., 'Account', 'Product', 'ProductItem')"
    )
