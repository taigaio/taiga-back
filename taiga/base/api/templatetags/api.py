# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# The code is partially taken (and modified) from django rest framework
# that is licensed under the following terms:
#
# Copyright (c) 2011-2014, Tom Christie
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.staticfiles.templatetags.staticfiles import StaticFilesNode
from django.http import QueryDict
from django.utils.encoding import iri_to_uri
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import smart_urlquote

from urllib import parse as urlparse

import re

register = template.Library()



@register.tag("static")
def do_static(parser, token):
    return StaticFilesNode.handle_token(parser, token)


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    query_dict = QueryDict(query).copy()
    query_dict[key] = val
    query = query_dict.urlencode()
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


# Regex for adding classes to html snippets
class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


# And the template tags themselves...

@register.simple_tag
def optional_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse("api:login")
    except NoReverseMatch:
        return ""

    snippet = "<a href='%s?next=%s'>Log in</a>" % (login_url, request.path)
    return snippet


@register.simple_tag
def optional_logout(request):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse("api:logout")
    except NoReverseMatch:
        return ""

    snippet = "<a href='%s?next=%s'>Log out</a>" % (logout_url, request.path)
    return snippet


@register.simple_tag
def add_query_param(request, key, val):
    """
    Add a query parameter to the current request url, and return the new url.
    """
    iri = request.get_full_path()
    uri = iri_to_uri(iri)
    return replace_query_param(uri, key, val)


@register.filter
def add_class(value, css_class):
    """
    http://stackoverflow.com/questions/4124220/django-adding-css-classes-when-rendering-form-fields-in-a-template

    Inserts classes into template variables that contain HTML tags,
    useful for modifying forms without needing to change the Form objects.

    Usage:

        {{ field.label_tag|add_class:"control-label" }}

    In the case of REST Framework, the filter is used to add Bootstrap-specific
    classes to the forms.
    """
    html = six.text_type(value)
    match = class_re.search(html)
    if match:
        m = re.search(r"^%s$|^%s\s|\s%s\s|\s%s$" % (css_class, css_class,
                                                    css_class, css_class),
                      match.group(1))
        if not m:
            return mark_safe(class_re.sub(match.group(1) + " " + css_class,
                                          html))
    else:
        return mark_safe(html.replace(">", ' class="%s">' % css_class, 1))
    return value


# Bunch of stuff cloned from urlize
TRAILING_PUNCTUATION = [".", ",", ":", ";", ".)", "\"", "'"]
WRAPPING_PUNCTUATION = [("(", ")"), ("<", ">"), ("[", "]"), ("&lt;", "&gt;"),
                        ("\"", "\""), ("'", "'")]
word_split_re = re.compile(r"(\s+)")
simple_url_re = re.compile(r"^https?://\[?\w", re.IGNORECASE)
simple_url_2_re = re.compile(r"^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)$", re.IGNORECASE)
simple_email_re = re.compile(r"^\S+@\S+\.\S+$")


def smart_urlquote_wrapper(matched_url):
    """
    Simple wrapper for smart_urlquote. ValueError("Invalid IPv6 URL") can
    be raised here, see issue #1386
    """
    try:
        return smart_urlquote(matched_url)
    except ValueError:
        return None


@register.filter
def urlize_quoted_links(text, trim_url_limit=None, nofollow=True, autoescape=True):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links, and also on links ending in one of
    the original seven gTLDs (.com, .edu, .gov, .int, .mil, .net, and .org).
    Links can have trailing punctuation (periods, commas, close-parens) and
    leading punctuation (opening parens) and it"ll still do the right thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ("%s..." % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_text(text))
    for i, word in enumerate(words):
        if "." in word or "@" in word or ":" in word:
            # Deal with punctuation.
            lead, middle, trail = "", word, ""
            for punctuation in TRAILING_PUNCTUATION:
                if middle.endswith(punctuation):
                    middle = middle[:-len(punctuation)]
                    trail = punctuation + trail
            for opening, closing in WRAPPING_PUNCTUATION:
                if middle.startswith(opening):
                    middle = middle[len(opening):]
                    lead = lead + opening
                # Keep parentheses at the end only if they"re balanced.
                if (middle.endswith(closing)
                    and middle.count(closing) == middle.count(opening) + 1):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ""
            if simple_url_re.match(middle):
                url = smart_urlquote_wrapper(middle)
            elif simple_url_2_re.match(middle):
                url = smart_urlquote_wrapper("http://%s" % middle)
            elif not ":" in middle and simple_email_re.match(middle):
                local, domain = middle.rsplit("@", 1)
                try:
                    domain = domain.encode("idna").decode("ascii")
                except UnicodeError:
                    continue
                url = "mailto:%s@%s" % (local, domain)
                nofollow_attr = ""

            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = mark_safe("%s%s%s" % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return "".join(words)


@register.filter
def break_long_headers(header):
    """
    Breaks headers longer than 160 characters (~page length)
    when possible (are comma separated)
    """
    if len(header) > 160 and "," in header:
        header = mark_safe("<br> " + ", <br>".join(header.split(",")))
    return header
