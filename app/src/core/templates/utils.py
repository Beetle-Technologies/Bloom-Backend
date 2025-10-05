import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.core.config import settings
from src.core.helpers.assets import image_to_base64


def setup_template_environment(env: Any):
    """Setup filters and globals for a Jinja2 environment."""

    env.filters["rawjson"] = json.dumps
    env.globals["STATIC_PREFIX"] = "/static/"
    env.globals["SERVER_URL"] = settings.server_url
    env.globals["FRONTEND_URL"] = settings.FRONTEND_URL
    env.globals["APP_NAME"] = settings.APP_NAME
    env.globals["APP_VERSION"] = settings.APP_VERSION
    env.globals["MAX_PASSWORD_RESET_TIME"] = settings.MAX_PASSWORD_RESET_TIME // 3600
    env.globals["SUPPORT_EMAIL"] = settings.SUPPORT_EMAIL
    env.globals["raw_image"] = image_to_base64
    env.globals["uuid4"] = uuid4
    env.globals["now"] = datetime.now
