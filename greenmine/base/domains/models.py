# -*- coding: utf-8 -*-

import string

from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from . import clear_domain_cache


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


class Domain(models.Model):
    domain = models.CharField(_('domain name'), max_length=255, unique=True,
                              validators=[_simple_domain_name_validator])
    name = models.CharField(_('display name'), max_length=255)
    scheme = models.CharField(_('scheme'), max_length=60, null=True, default=None)

    # Site Metadata
    public_register = models.BooleanField(default=False)
    default_language = models.CharField(max_length=20, null=False, blank=True, default="",
                                        verbose_name=_("default language"))

    class Meta:
        verbose_name = _('domain')
        verbose_name_plural = _('domain')
        ordering = ('domain',)

    def __str__(self):
        return self.domain


class DomainMember(models.Model):
    domain = models.ForeignKey("Domain", related_name="+", null=True)
    user = models.ForeignKey("users.User", related_name="+", null=True)

    email = models.EmailField(max_length=255)
    is_owner = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    class Meta:
        ordering = ["email"]
        verbose_name = "Domain Member"
        verbose_name_plural = "Domain Members"
        unique_together = ("domain", "user")

    def __str__(self):
        return "DomainMember: {0}:{1}".format(self.domain, self.user)


pre_save.connect(clear_domain_cache, sender=Domain)
pre_delete.connect(clear_domain_cache, sender=Domain)
