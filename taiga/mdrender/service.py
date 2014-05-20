import hashlib
import functools

from django.core.cache import cache
from django.utils.encoding import force_bytes

from markdown import markdown
from fn import F

from .gfm import AutolinkExtension
from .gfm import AutomailExtension
from .gfm import HiddenHiliteExtension
from .gfm import SemiSaneListExtension
from .gfm import SpacedLinkExtension
from .gfm import StrikethroughExtension
from .gfm import WikiLinkExtension
from .gfm import EmojifyExtension

from .processors.mentions import mentions
from .processors.references import references


def _make_extensions_list(wikilinks_config=None):
    return [AutolinkExtension(),
            AutomailExtension(),
            SemiSaneListExtension(),
            SpacedLinkExtension(),
            StrikethroughExtension(),
            WikiLinkExtension(wikilinks_config),
            EmojifyExtension(),
            "extra",
            "codehilite"]


import diff_match_patch


def cache_by_sha(func):
    @functools.wraps(func)
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
    wikilinks_config = {"base_url": "#/project/{}/wiki/".format(project.slug),
                        "end_url": ""}
    extensions = _make_extensions_list(wikilinks_config=wikilinks_config)
    return markdown(text, extensions=extensions)


def _preprocessors(project, text):
    pre = F() >> mentions >> F(references, project)
    return pre(text)


#@cache_by_sha
def render(project, text):
    renderer = F() >> F(_preprocessors, project) >> F(_render_markdown, project)
    return renderer(text)

class DiffMatchPatch(diff_match_patch.diff_match_patch):
    def diff_pretty_html(self, diffs):
        html = []
        for (op, data) in diffs:
          text = (data.replace("&", "&amp;").replace("<", "&lt;")
                     .replace(">", "&gt;").replace("\n", "<br />"))
          if op == self.DIFF_INSERT:
            html.append("<ins style=\"background:#e6ffe6;\">%s</ins>" % text)
          elif op == self.DIFF_DELETE:
            html.append("<del style=\"background:#ffe6e6;\">%s</del>" % text)
          elif op == self.DIFF_EQUAL:
            html.append("<span>%s</span>" % text)
        return "".join(html)

def get_diff_of_htmls(html1, html2):
    diffutil = DiffMatchPatch()
    diff = diffutil.diff_main(html1, html2)
    return diffutil.diff_pretty_html(diff)

__all__ = ['render', 'get_diff_of_htmls']
