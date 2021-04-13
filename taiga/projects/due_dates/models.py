from django.db import models
from django.utils.translation import ugettext_lazy as _


class DueDateMixin(models.Model):
    due_date = models.DateField(
        blank=True, null=True, default=None, verbose_name=_('due date'),
    )
    due_date_reason = models.TextField(
        null=False, blank=True, default='', verbose_name=_('reason for the due date'),
    )

    class Meta:
        abstract = True
