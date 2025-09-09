from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemBytecodeCache, FileSystemLoader, select_autoescape
from src.core.config import settings
from src.core.templates.utils import setup_template_environment

JINJA2_CACHE_PATH = f"{settings.BASE_DIR}/.jinja2_cache"

if not Path(JINJA2_CACHE_PATH).exists():
    Path(JINJA2_CACHE_PATH).mkdir(parents=True)
    Path(JINJA2_CACHE_PATH).chmod(0o700)

JINJA2_ENVIRONMENT = Environment(
    loader=FileSystemLoader(settings.JINJA_TEMPLATES_DIR),
    auto_reload=settings.ENVIRONMENT == "local",
    autoescape=select_autoescape(["html", "xml"]),
    extensions=["jinja2.ext.do"],
    trim_blocks=True,
    lstrip_blocks=True,
    optimized=True,
    cache_size=1000,
    bytecode_cache=FileSystemBytecodeCache(directory=JINJA2_CACHE_PATH),
)

templates = Jinja2Templates(env=JINJA2_ENVIRONMENT)

setup_template_environment(templates.env)
