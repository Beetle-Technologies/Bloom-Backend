from pydantic import BaseModel


class LocalConfiguration(BaseModel):
    """
    Schema for local storage provider.

    Attributes:
        base_path (str): The base path for storing files.
    """

    base_path: str


class S3Configuration(BaseModel):
    """
    Schema for S3 storage provider.

    Attributes:
        bucket_name (str): The S3 bucket name.
        region_name (str): The AWS region name.
        access_key_id (str): AWS access key ID.
        secret_access_key (str): AWS secret access key.
        endpoint_url (str | None): Custom endpoint URL for S3-compatible services.
    """

    bucket_name: str
    region_name: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: str | None = None


class CloudinaryConfiguration(BaseModel):
    """
    Schema for Cloudinary storage provider.

    Attributes:
        cloud_name (str): Cloudinary cloud name.
        api_key (str): Cloudinary API key.
        api_secret (str): Cloudinary API secret.
    """

    cloud_name: str
    api_key: str
    api_secret: str
