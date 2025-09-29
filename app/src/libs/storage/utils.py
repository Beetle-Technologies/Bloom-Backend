import base64
import hashlib
import mimetypes
from datetime import datetime

from PIL import Image

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
]


def generate_file_key(filename: str, attachable_type: str, attachable_id: str) -> str:
    """
    Generate a unique file key for storage.

    Args:
        filename: The original filename
        attachable_type: The type of attachable entity
        attachable_id: The ID of the attachable entity

    Returns:
        str: A unique file key
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_input = f"{attachable_type}_{attachable_id}_{filename}_{timestamp}"
    hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:8]

    attachable_id_hex = base64.b64encode(attachable_id.encode()).decode()
    name_part, _, ext_part = filename.rpartition(".")
    if ext_part:
        return f"{attachable_type}/{attachable_id_hex}/{name_part}_{hash_digest}.{ext_part}"
    else:
        return f"{attachable_type}/{attachable_id_hex}/{name_part}_{hash_digest}"


def get_file_info(file_content: bytes, filename: str) -> tuple[str, str | None, float]:
    """
    Get file information from content and filename.

    Args:
        file_content: The file content as bytes
        filename: The original filename

    Returns:
        tuple: (mime_type, file_extension, file_size)
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"

    file_extension = None
    if "." in filename:
        file_extension = filename.split(".")[-1].lower()

    file_size = len(file_content)

    return mime_type, file_extension, file_size


def is_image(mime_type: str) -> bool:
    """
    Check if the MIME type is an image.

    Args:
        mime_type: The MIME type to check

    Returns:
        bool: True if it's an image type
    """
    return mime_type.startswith("image/")


async def generate_thumbnail(file_content: bytes, mime_type: str, size: tuple[int, int] = (200, 200)) -> bytes | None:
    """
    Generate a thumbnail for an image.

    Args:
        file_content: The image file content
        mime_type: The MIME type of the image
        size: The desired thumbnail size

    Returns:
        bytes | None: The thumbnail content or None if generation fails
    """
    if not is_image(mime_type):
        return None

    try:
        from io import BytesIO

        image = Image.open(BytesIO(file_content))
        image.thumbnail(size)
        output = BytesIO()
        image.save(output, format="JPEG")
        return output.getvalue()
    except Exception:
        return None


async def generate_preview(file_content: bytes, mime_type: str, size: tuple[int, int] = (800, 600)) -> bytes | None:
    """
    Generate a preview image.

    Args:
        file_content: The image file content
        mime_type: The MIME type of the image
        size: The desired preview size

    Returns:
        bytes | None: The preview content or None if generation fails
    """
    if not is_image(mime_type):
        return None

    try:
        from io import BytesIO

        image = Image.open(BytesIO(file_content))
        image.thumbnail(size)
        output = BytesIO()
        image.save(output, format="JPEG")
        return output.getvalue()
    except Exception:
        return None


def calculate_checksum(file_content: bytes) -> str:
    """
    Calculate MD5 checksum of file content.

    Args:
        file_content: The file content

    Returns:
        str: The MD5 checksum
    """
    return hashlib.md5(file_content).hexdigest()
