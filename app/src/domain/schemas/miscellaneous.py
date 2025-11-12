from typing import Literal

from pydantic import BaseModel, Field


class GenerateGIDRequest(BaseModel):
    """
    Schema for the request body to generate a new GID.
    """

    resource_type: Literal["Product", "ProductItem"] = Field(
        ..., description="The resource type for the GID (e.g., 'Product', 'ProductItem')"
    )
