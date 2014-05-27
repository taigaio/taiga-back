from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models


class Fan(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False, related_name="fans",
                                verbose_name=_("project"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                             related_name="fans", verbose_name=_("fans"))

    class Meta:
        verbose_name = _("Star")
        verbose_name_plural = _("Stars")
        unique_together = ("project", "user")

    def __unicode__(self):
        return self.user

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(*args, **kwargs)


class Stars(models.Model):
    project = models.OneToOneField("projects.Project", null=False, blank=False,
                                   verbose_name=_("project"))
    count = models.PositiveIntegerField(null=False, blank=False, default=0,
                                        verbose_name=_("count"))

    class Meta:
        verbose_name = _("Stars")
        verbose_name_plural = _("Stars")

    def __unicode__(self):
        return "{} stars".format(self.count)
