import hashlib
from django.core.cache import cache
from django.utils.encoding import force_bytes
from markdown import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
from .gfm import (AutolinkExtension, AutomailExtension, HiddenHiliteExtension,
                  SemiSaneListExtension, SpacedLinkExtension,
                  StrikethroughExtension)
from .processors.emoji import emoji
from .processors.mentions import mentions
from .processors.references import references

from fn import F

def cache_by_sha(func):
    def _decorator(project, text):
        sha1_hash = hashlib.sha1(force_bytes(text)).hexdigest()
        key = "{}-{}".format(sha1_hash, project.id)

        # Try to get it from the cache
        cached = cache.get(key)
        if cached is not None:
            return cached

        returned_value = func(text)

        cache.set(key, returned_value, timeout=None)
        return returned_value

    return _decorator

def _render_markdown(project, text):
    wikilinks_config = {
        "base_url": "#/project/{}/wiki/".format(project.slug),
        "end_url": ""
    }
    return markdown(text, extensions=[
        AutolinkExtension(), AutomailExtension(),
        SemiSaneListExtension(), SpacedLinkExtension(),
        StrikethroughExtension(), WikiLinkExtension(wikilinks_config), "extra",
        "codehilite"
    ])

def _preprocessors(project, text):
    pre = F() >> mentions >> F(references, project)
    return pre(text)

def _postprocessors(project, html):
    post = F() >> emoji
    return post(html)

#@cache_by_sha
def render(project, text):
    renderer = F() >> F(_preprocessors, project) >> F(_render_markdown, project) >> F(_postprocessors, project)

    return renderer(text)

__all__ = ['render']
