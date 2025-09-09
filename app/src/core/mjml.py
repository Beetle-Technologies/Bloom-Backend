from pathlib import Path
from typing import Any

import mjml
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemBytecodeCache, FileSystemLoader, Template, select_autoescape
from src.core.config import settings
from src.core.templates.utils import setup_template_environment


class MjmlTemplate(Template):
    """Custom MJML template that renders to HTML via mjml2html."""

    def render(self, *args: Any, **kwargs: Any) -> str:
        """
        Render MJML markup template to HTML.

        Args:
            *args: Positional arguments for the template.
            **kwargs: Keyword arguments for the template.

        Returns:
            str: Rendered HTML string.
        """

        markup = super().render(*args, **kwargs)
        result = mjml.mjml2html(markup)
        return result


class MjmlEnvironment(Environment):
    """Custom Jinja2 environment that uses MjmlTemplate for rendering."""

    template_class = MjmlTemplate


MJML_CACHE_PATH = f"{settings.BASE_DIR}/.mjml_cache"

if not Path(MJML_CACHE_PATH).exists():
    Path(MJML_CACHE_PATH).mkdir(parents=True)
    Path(MJML_CACHE_PATH).chmod(0o700)

MJML_ENVIRONMENT = MjmlEnvironment(
    loader=FileSystemLoader(settings.MJML_TEMPLATES_DIR),
    auto_reload=settings.ENVIRONMENT == "local",
    autoescape=select_autoescape(["html", "xml"]),
    extensions=["jinja2.ext.do"],
    trim_blocks=True,
    lstrip_blocks=True,
    optimized=True,
    cache_size=1000,
    bytecode_cache=FileSystemBytecodeCache(directory=f"{settings.BASE_DIR}/.mjml_cache"),
)

mjml_templates = Jinja2Templates(env=MJML_ENVIRONMENT)

setup_template_environment(mjml_templates.env)
