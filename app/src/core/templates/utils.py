import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.core.config import settings
from src.core.security import generate_csrf


def setup_template_environment(env: Any):
    """Setup filters and globals for a Jinja2 environment."""

    env.filters["rawjson"] = json.dumps
    env.globals["STATIC_PREFIX"] = "/static/"
    env.globals["SERVER_URL"] = settings.server_url
    env.globals["APP_NAME"] = settings.APP_NAME
    env.globals["APP_VERSION"] = settings.APP_VERSION
    env.globals["uuid4"] = uuid4
    env.globals["csrf"] = generate_csrf
    env.globals["now"] = datetime.now
