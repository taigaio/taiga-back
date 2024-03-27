# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC
#
# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import DenylistedToken, OutstandingToken


@admin.register(OutstandingToken)
class OutstandingTokenAdmin(admin.ModelAdmin):
    list_display = (
        'jti',
        'user',
        'created_at',
        'expires_at',
    )
    search_fields = (
        'user__id',
        'jti',
    )
    ordering = (
        'user',
    )

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        return qs.select_related('user')

    # Read-only behavior defined below
    actions = None

    def get_readonly_fields(self, *args, **kwargs):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        return (
            request.method in ['GET', 'HEAD'] and  # noqa: W504
            super().has_change_permission(request, obj)
        )




@admin.register(DenylistedToken)
class DenylistedTokenAdmin(admin.ModelAdmin):
    list_display = (
        'token_jti',
        'token_user',
        'token_created_at',
        'token_expires_at',
        'denylisted_at',
    )
    search_fields = (
        'token__user__id',
        'token__jti',
    )
    ordering = (
        'token__user',
    )

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        return qs.select_related('token__user')

    @admin.display(
        description=_('jti'),
        ordering='token__jti',
    )
    def token_jti(self, obj):
        return obj.token.jti

    @admin.display(
        description=_('user'),
        ordering='token__user',
    )
    def token_user(self, obj):
        return obj.token.user

    @admin.display(
        description=_('created at'),
        ordering='token__created_at',
    )
    def token_created_at(self, obj):
        return obj.token.created_at

    @admin.display(
        description=_('expires at'),
        ordering='token__expires_at',
    )
    def token_expires_at(self, obj):
        return obj.token.expires_at


