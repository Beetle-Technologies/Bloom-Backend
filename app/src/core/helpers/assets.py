import base64
from pathlib import Path

from src.core.config import settings


def image_to_base64(image_path: str) -> str:
    """
    Convert an image file to a base64-encoded string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64-encoded string of the image.
    """
    full_image_path = Path(settings.BASE_DIR) / "static" / "images" / image_path
    img_ext = full_image_path.suffix.lower()

    if not full_image_path.exists() or not full_image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {full_image_path}")

    with open(full_image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/{img_ext};base64,{encoded_string}"
