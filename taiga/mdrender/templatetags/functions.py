# -*- coding: utf-8 -*-
from django_jinja import library
from jinja2 import Markup
from taiga.mdrender.service import render


@library.global_function
def mdrender(project, text) -> str:
    if text:
        return Markup(render(project, text))
    return ""
