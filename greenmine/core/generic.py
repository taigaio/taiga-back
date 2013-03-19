# -*- coding: utf-8 -*-

from django.views.decorators.cache import cache_page
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.template import RequestContext, loader
from django.contrib import messages
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from superview.views import SuperView as View

from greenmine.core import permissions
from greenmine.core.middleware import PermissionDeniedException


class GenericView(View):
    """ Generic view with some util methods. """

    def render_to_ok(self, context={}):
        response = {'valid': True, 'errors': []}
        response.update(context)
        return self.render_json(response, ok=True)

    def render_to_error(self, context={}):
        response = {'valid': False, 'errors': []}
        response.update(context)
        return self.render_json(response, ok=False)

    def redirect_referer(self, msg=None):
        if msg is not None:
            messages.info(self.request, msg)

        referer = self.request.META.get('HTTP_REFERER', '/')
        return self.render_redirect(referer)

    def check_role(self, user, project, perms, exception=PermissionDeniedException):
        ok = permissions.has_perms(user, project, perms)
        if exception is not None and not ok:
            raise exception()
        return ok
