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

"""
Renderers are used to serialize a response into specific media types.

They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.

REST framework also provides an HTML renderer the renders the browsable API.
"""

from django.core.exceptions import ImproperlyConfigured
from django.http.multipartparser import parse_header
from django.template import RequestContext, loader, Template
from django.test.client import encode_multipart
from django.utils import six

from .utils import encoders

import json


class BaseRenderer(object):
    """
    All renderers should extend this class, setting the `media_type`
    and `format` attributes, and override the `.render()` method.
    """

    media_type = None
    format = None
    charset = "utf-8"
    render_style = "text"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        raise NotImplemented("Renderer class requires .render() to be implemented")


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON.
    Applies JSON's backslash-u character escaping for non-ascii characters.
    """

    media_type = "application/json"
    format = "json"
    encoder_class = encoders.JSONEncoder
    ensure_ascii = True
    charset = None
    # JSON is a binary encoding, that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/

    def _get_indent(self, accepted_media_type, renderer_context):
        # If "indent" is provided in the context, then pretty print the result.
        # E.g. If we"re being called by the BrowsableAPIRenderer.
        renderer_context = renderer_context or {}
        indent = renderer_context.get("indent", None)

        if accepted_media_type:
            # If the media type looks like "application/json; indent=4",
            # then pretty print the result.
            base_media_type, params = parse_header(accepted_media_type.encode("ascii"))
            indent = params.get("indent", indent)
            try:
                indent = max(min(int(indent), 8), 0)
            except (ValueError, TypeError):
                indent = None

        return indent

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON.
        """
        if data is None:
            return bytes()

        indent = self._get_indent(accepted_media_type, renderer_context)

        ret = json.dumps(data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii)

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            return bytes(ret.encode("utf-8"))
        return ret

    def render_to_file(self, data, outputfile, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into a file with JSON format.
        """
        if data is None:
            return bytes()

        indent = self._get_indent(accepted_media_type, renderer_context)

        ret = json.dump(data, outputfile, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii)


class UnicodeJSONRenderer(JSONRenderer):
    ensure_ascii = False
    """
    Renderer which serializes to JSON.
    Does *not* apply JSON's character escaping for non-ascii characters.
    """


class JSONPRenderer(JSONRenderer):
    """
    Renderer which serializes to json,
    wrapping the json output in a callback function.
    """

    media_type = "application/javascript"
    format = "jsonp"
    callback_parameter = "callback"
    default_callback = "callback"
    charset = "utf-8"

    def get_callback(self, renderer_context):
        """
        Determine the name of the callback to wrap around the json output.
        """
        request = renderer_context.get("request", None)
        params = request and request.QUERY_PARAMS or {}
        return params.get(self.callback_parameter, self.default_callback)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders into jsonp, wrapping the json output in a callback function.

        Clients may set the callback function name using a query parameter
        on the URL, for example: ?callback=exampleCallbackName
        """
        renderer_context = renderer_context or {}
        callback = self.get_callback(renderer_context)
        json = super(JSONPRenderer, self).render(data, accepted_media_type,
                                                 renderer_context)
        return callback.encode(self.charset) + b"(" + json + b");"


class TemplateHTMLRenderer(BaseRenderer):
    """
    An HTML renderer for use with templates.

    The data supplied to the Response object should be a dictionary that will
    be used as context for the template.

    The template name is determined by (in order of preference):

    1. An explicit `.template_name` attribute set on the response.
    2. An explicit `.template_name` attribute set on this class.
    3. The return result of calling `view.get_template_names()`.

    For example:
        data = {"users": User.objects.all()}
        return Response(data, template_name="users.html")

    For pre-rendered HTML, see StaticHTMLRenderer.
    """

    media_type = "text/html"
    format = "html"
    template_name = None
    exception_template_names = [
        "%(status_code)s.html",
        "api_exception.html"
    ]
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders data to HTML, using Django's standard template rendering.

        The template name is determined by (in order of preference):

        1. An explicit .template_name set on the response.
        2. An explicit .template_name set on this class.
        3. The return result of calling view.get_template_names().
        """
        renderer_context = renderer_context or {}
        view = renderer_context["view"]
        request = renderer_context["request"]
        response = renderer_context["response"]

        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)

        context = self.resolve_context(data, request, response)
        return template.render(context)

    def resolve_template(self, template_names):
        return loader.select_template(template_names)

    def resolve_context(self, data, request, response):
        if response.exception:
            data["status_code"] = response.status_code
        return RequestContext(request, data)

    def get_template_names(self, response, view):
        if response.template_name:
            return [response.template_name]
        elif self.template_name:
            return [self.template_name]
        elif hasattr(view, "get_template_names"):
            return view.get_template_names()
        elif hasattr(view, "template_name"):
            return [view.template_name]
        raise ImproperlyConfigured("Returned a template response with no `template_name` attribute set on either the view or response")

    def get_exception_template(self, response):
        template_names = [name % {"status_code": response.status_code}
                          for name in self.exception_template_names]

        try:
            # Try to find an appropriate error template
            return self.resolve_template(template_names)
        except Exception:
            # Fall back to using eg "404 Not Found"
            return Template("%d %s" % (response.status_code,
                                       response.status_text.title()))


# Note, subclass TemplateHTMLRenderer simply for the exception behavior
class StaticHTMLRenderer(TemplateHTMLRenderer):
    """
    An HTML renderer class that simply returns pre-rendered HTML.

    The data supplied to the Response object should be a string representing
    the pre-rendered HTML content.

    For example:
        data = "<html><body>example</body></html>"
        return Response(data)

    For template rendered HTML, see TemplateHTMLRenderer.
    """
    media_type = "text/html"
    format = "html"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context["response"]

        if response and response.exception:
            request = renderer_context["request"]
            template = self.get_exception_template(response)
            context = self.resolve_context(data, request, response)
            return template.render(context)

        return data


class MultiPartRenderer(BaseRenderer):
    media_type = "multipart/form-data; boundary=BoUnDaRyStRiNg"
    format = "multipart"
    charset = "utf-8"
    BOUNDARY = "BoUnDaRyStRiNg"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return encode_multipart(self.BOUNDARY, data)
