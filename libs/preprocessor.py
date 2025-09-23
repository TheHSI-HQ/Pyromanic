from flask import render_template as _render_template, render_template_string as _render_template_string
from jinja2.environment import Template
from libs.config import load_reloading_config, read_config
import typing as t

cfg = load_reloading_config('pyromanic.yaml')

def render_template(
    template_name_or_list: str | Template | list[str | Template],
    **context: t.Any,
) -> str:
    """Render a template by name with the given context.

    :param template_name_or_list: The name of the template to render. If
        a list is given, the first name to exist will be rendered.
    :param context: The variables to make available in the template.
    """

    base = read_config(cfg(), "app.base_path", str)
    title = str(read_config(cfg(), "app.branding.name", str))
    raw_title = title
    if title == "default":
        title = "Pyromanic"
        raw_title = "Pyromanic"
    else:
        title = title + " - Pyromanic"
    context["title"] = title
    context["raw_title"] = raw_title
    context["base"] = base
    return _render_template(template_name_or_list, **context)

def render_template_string(source: str, **context: t.Any) -> str:
    """Render a template from the given source string with the given
    context.

    :param source: The source code of the template to render.
    :param context: The variables to make available in the template.
    """

    base = read_config(cfg(), "app.base_path", str)
    title = str(read_config(cfg(), "app.branding.name", str))
    raw_title = title
    if title == "default":
        title = "Pyromanic"
        raw_title = "Pyromanic"
    else:
        title = title + " - Pyromanic"
    context["title"] = title
    context["raw_title"] = raw_title
    context["base"] = base
    return _render_template_string(source, **context)