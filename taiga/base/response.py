# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

"""The various HTTP responses for use in returning proper HTTP codes."""
from http.client import responses

from django import http

from django.template.response import SimpleTemplateResponse
from django.utils import six


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that allows its data to be rendered into
    arbitrary media types.
    """
    def __init__(self, data=None, status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'template_name', and instead use 'data'.

        Setting 'renderer' and 'media_type' will typically be deferred,
        For example being set automatically by the `APIView`.
        """
        super().__init__(None, status=status)
        self.data = data
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        if headers:
            for name, value in six.iteritems(headers):
                self[name] = value

    @property
    def rendered_content(self):
        renderer = getattr(self, "accepted_renderer", None)
        media_type = getattr(self, "accepted_media_type", None)
        context = getattr(self, "renderer_context", None)

        assert renderer, ".accepted_renderer not set on Response"
        assert media_type, ".accepted_media_type not set on Response"
        assert context, ".renderer_context not set on Response"
        context["response"] = self

        charset = renderer.charset
        content_type = self.content_type

        if content_type is None and charset is not None:
            content_type = "{0}; charset={1}".format(media_type, charset)
        elif content_type is None:
            content_type = media_type
        self["Content-Type"] = content_type

        ret = renderer.render(self.data, media_type, context)
        if isinstance(ret, six.text_type):
            assert charset, "renderer returned unicode, and did not specify " \
            "a charset value."
            return bytes(ret.encode(charset))

        if not ret:
            del self["Content-Type"]

        return ret

    @property
    def status_text(self):
        """
        Returns reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        # TODO: Deprecate and use a template tag instead
        # TODO: Status code text for RFC 6585 status codes
        return responses.get(self.status_code, '')

    def __getstate__(self):
        """
        Remove attributes from the response that shouldn't be cached
        """
        state = super().__getstate__()
        for key in ("accepted_renderer", "renderer_context", "data"):
            if key in state:
                del state[key]
        return state


class Ok(Response):
    """200 OK

    Should be used to indicate nonspecific success. Must not be used to
    communicate errors in the response body.
    In most cases, 200 is the code the client hopes to see. It indicates that
    the REST API successfully carried out whatever action the client requested,
    and that no more specific code in the 2xx series is appropriate. Unlike
    the 204 status code, a 200 response should include a response body.
    """
    status_code = 200


class Created(Response):
    """201 Created

    Must be used to indicate successful resource creation.
    A REST API responds with the 201 status code whenever a collection creates,
    or a store adds, a new resource at the client's request. There may also be
    times when a new resource is created as a result of some controller action,
    in which case 201 would also be an appropriate response.
    """
    status_code = 201


class Accepted(Response):
    """202 Accepted

    Must be used to indicate successful start of an asynchronous action.
    A 202 response indicates that the client's request will be handled
    asynchronously. This response status code tells the client that the request
    appears valid, but it still may have problems once it's finally processed.
    A 202 response is typically used for actions that take a long while to
    process.
    Controller resources may send 202 responses, but other resource types
    should not.
    """
    status_code = 202


class NoContent(Response):
    """204 No Content

    Should be used when the response body is intentionally empty.
    The 204 status code is usually sent out in response to a PUT, POST, or
    DELETE request, when the REST API declines to send back any status message
    or representation in the response message's body. An API may also send 204
    in conjunction with a GET request to indicate that the requested resource
    exists, but has no state representation to include in the body.
    """
    status_code = 204


class MultipleChoices(Response):
    """300 Multiple Choices

    Indicates multiple options for the resource that the client may follow.
    It could be used to present different format options for video, list files
    with different extensions, or word sense disambiguation.
    """
    status_code = 300


class MovedPermanently(http.HttpResponsePermanentRedirect):
    """301 Moved Permanently

    Should be used to relocate resources.
    The 301 status code indicates that the REST API's resource model has been
    significantly redesigned and a new permanent URI has been assigned to the
    client's requested resource. The REST API should specify the new URI in
    the response's Location header.
    """
    status_code = 301


class Found(http.HttpResponseRedirect):
    """302 Found

    Should not be used.
    The intended semantics of the 302 response code have been misunderstood
    by programmers and incorrectly implemented in programs since version 1.0
    of the HTTP protocol.
    The confusion centers on whether it is appropriate for a client to always
    automatically issue a follow-up GET request to the URI in response's
    Location header, regardless of the original request's method. For the
    record, the intent of 302 is that this automatic redirect behavior only
    applies if the client's original request used either the GET or HEAD
    method.
    To clear things up, HTTP 1.1 introduced status codes 303 ("See Other")
    and 307 ("Temporary Redirect"), either of which should be used
    instead of 302.
    """
    status_code = 302


class SeeOther(Response):
    """303 See Other

    Should be used to refer the client to a different URI.
    A 303 response indicates that a controller resource has finished its work,
    but instead of sending a potentially unwanted response body, it sends the
    client the URI of a response resource. This can be the URI of a temporary
    status message, or the URI to some already existing, more permanent,
    resource.
    Generally speaking, the 303 status code allows a REST API to send a
    reference to a resource without forcing the client to download its state.
    Instead, the client may send a GET request to the value of the Location
    header.
    """
    status_code = 303


class NotModified(http.HttpResponseNotModified):
    """304 Not Modified

    Should be used to preserve bandwith.
    This status code is similar to 204 ("No Content") in that the response body
    must be empty. The key distinction is that 204 is used when there is
    nothing to send in the body, whereas 304 is used when there is state
    information associated with a resource but the client already has the most
    recent version of the representation.
    """
    status_code = 304


class TemporaryRedirect(Response):
    """307 Temporary Redirect

    Should be used to tell clients to resubmit the request to another URI.
    HTTP/1.1 introduced the 307 status code to reiterate the originally
    intended semantics of the 302 ("Found") status code. A 307 response
    indicates that the REST API is not going to process the client's request.
    Instead, the client should resubmit the request to the URI specified by
    the response message's Location header.
    A REST API can use this status code to assign a temporary URI to the
    client's requested resource. For example, a 307 response can be used to
    shift a client request over to another host.
    """
    status_code = 307


class BadRequest(Response):
    """400 Bad Request

    May be used to indicate nonspecific failure.
    400 is the generic client-side error status, used when no other 4xx error
    code is appropriate.
    """
    status_code = 400


class Unauthorized(Response):
    """401 Unauthorized

    Must be used when there is a problem with the client credentials.
    A 401 error response indicates that the client tried to operate on a
    protected resource without providing the proper authorization. It may have
    provided the wrong credentials or none at all.
    """
    status_code = 401


class Forbidden(Response):
    """403 Forbidden

    Should be used to forbid access regardless of authorization state.
    A 403 error response indicates that the client's request is formed
    correctly, but the REST API refuses to honor it. A 403 response is not a
    case of insufficient client credentials; that would be 401 ("Unauthorized").
    REST APIs use 403 to enforce application-level permissions. For example, a
    client may be authorized to interact with some, but not all of a REST API's
    resources. If the client attempts a resource interaction that is outside of
    its permitted scope, the REST API should respond with 403.
    """
    status_code = 403


class NotFound(Response):
    """404 Not Found

    Must be used when a client's URI cannot be mapped to a resource.
    The 404 error status code indicates that the REST API can't map the
    client's URI to a resource.
    """
    status_code = 404


class MethodNotAllowed(Response):
    """405 Method Not Allowed

    Must be used when the HTTP method is not supported.
    The API responds with a 405 error to indicate that the client tried to use
    an HTTP method that the resource does not allow. For instance, a read-only
    resource could support only GET and HEAD, while a controller resource might
    allow GET and POST, but not PUT or DELETE.
    A 405 response must include the Allow header, which lists the HTTP methods
    that the resource supports. For example:

        Allow: GET, POST

    """
    status_code = 405


class NotAcceptable(Response):
    """406 Not Acceptable

    Must be used when the requested media type cannot be served.
    The 406 error response indicates that the API is not able to generate any
    of the client's preferred media types, as indicated by the Accept request
    header. For example, a client request for data formatted as application/xml
    will receive a 406 response if the API is only willing to format data as
    application/json.
    """
    status_code = 406


class Conflict(Response):
    """409 Conflict

    Should be used to indicate a violation of the resource state.
    The 409 error response tells the client that they tried to put the REST
    API's resources into an impossible or inconsistent state. For example, a
    REST API may return this response code when a client tries to delete a
    non-empty store resource.
    """
    status_code = 409


class Gone(Response):
    """410 Gone

    Indicates that the resource requested is no longer available and will not
    be available again.
    This should be used when a resource has been intentionally removed and the
    resource should be purged. Upon receiving a 410 status code, the client
    should not request the resource again in the future.
    """
    status_code = 410


class PreconditionFailed(Response):
    """412 Precondition Failed

    Should be used to support conditional operations.
    The 412 error response indicates that the client specified one or more
    preconditions in its request headers, effectively telling the REST API to
    carry out its request only if certain conditions were met.
    A 412 response indicates that those conditions were not met, so instead of
    carrying out the request, the API sends this status code.
    """
    status_code = 412


class UnsupportedMediaType(Response):
    """415 Unsupported Media Type

    Must be used when the media type of a request's payload cannot be processed.
    The 415 error response indicates that the API is not able to process the
    client's supplied media type, as indicated by the Content-Type request
    header.
    For example, a client request including data formatted as application/xml
    will receive a 415 response if the API is only willing to process data
    formatted as application/json.
    """
    status_code = 415


class TooManyRequests(Response):
    """429 Too Many Requests

    The user has sent too many requests in a given amount of time.
    Intended for use with rate limiting schemes.
    """
    status_code = 429


class InternalServerError(Response):
    """500 Internal Server Error

    Should be used to indicate API malfunction.
    500 is the generic REST API error response. Most web frameworks
    automatically respond with this response status code whenever they execute
    some request handler code that raises an exception.
    A 500 error is never the client's fault and therefore it is reasonable for
    the client to retry the exact same request that triggered this response,
    and hope to get a different response.
    """
    status_code = 500


class NotImplemented(Response):
    """501 Not Implemented

    The server either does not recognise the request method, or it lacks the
    ability to fulfill the request.
    """
    status_code = 501
