# -*- coding: utf-8 -*-

import string

from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from . import sites


def _simple_domain_name_validator(value):
    """
    Validates that the given value contains no whitespaces to prevent common
    typos.
    """
    if not value:
        return
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            _("The domain name cannot contain any spaces or tabs."),
            code='invalid',
        )


class Site(models.Model):
    domain = models.CharField(_('domain name'), max_length=255, unique=True,
                              validators=[_simple_domain_name_validator])
    name = models.CharField(_('display name'), max_length=255)
    scheme = models.CharField(_('scheme'), max_length=60, null=True, default=None)

    # Site Metadata
    public_register = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')
        ordering = ('domain',)

    def __str__(self):
        return self.domain


class SiteMember(models.Model):
    site = models.ForeignKey("Site", related_name="+")
    user = models.ForeignKey("users.User", related_name="+", null=True)

    email = models.EmailField(max_length=255)
    is_owner = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    class Meta:
        ordering = ["email"]
        verbose_name = "Site Member"
        verbose_name_plural = "Site Members"
        unique_together = ("site", "user")

    def __str__(self):
        return "SiteMember: {0}:{1}".format(self.site, self.user)


pre_save.connect(sites.clear_site_cache, sender=Site)
pre_delete.connect(sites.clear_site_cache, sender=Site)


# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from . import monkey
monkey.patch_api_view()
monkey.patch_serializer()
monkey.patch_import_module()
monkey.patch_south_hacks()
