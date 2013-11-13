# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _

import reversion


class WatcherMixin(models.Model):
    NOTIFY_LEVEL_CHOICES = (
        ("all_owned_projects", _(u"All events on my projects")),
        ("only_watching", _(u"Only events for objects i watch")),
        ("only_assigned", _(u"Only events for objects assigned to me")),
        ("only_owner", _(u"Only events for objects owned by me")),
        ("no_events", _(u"No events")),
    )

    notify_level = models.CharField(max_length=32, null=False, blank=False,
                                    default="all_owned_projects",
                                    choices=NOTIFY_LEVEL_CHOICES,
                                    verbose_name=_(u"notify level"))
    notify_changes_by_me = models.BooleanField(blank=True, default=False,
                                               verbose_name=_(u"notify changes by me"))

    class Meta:
        abstract = True

    def allow_notify_owned(self):
        return (self.notify_level in [
            "only_owner",
            "only_assigned",
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_assigned_to(self):
        return (self.notify_level in [
            "only_assigned",
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_suscribed(self):
        return (self.notify_level in [
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_project(self, project):
        return self.notify_level == "all_owned_projects" and project.owner.pk == self.pk

    def allow_notify_by_me(self, changer):
        return (changer.pk != self.pk) or self.notify_changes_by_me


class WatchedMixin(models.Model):
    notifiable_fields = []

    class Meta:
        abstract = True

    @property
    def last_version(self):
        version_list = reversion.get_for_object(self)
        return version_list and version_list[0] or None

    def get_changed_fields_list(self, data_dict):
        def _key_by_notifiable_field(item):
            try:
                return self.notifiable_fields.index(item["name"])
            except ValueError:
                return 100000 # Emulate the maximum value

        if self.notifiable_fields:
            changed_data = {k:v for k, v in data_dict.items()
                                    if k in self.notifiable_fields}
        else:
            changed_data = data_dict

        fields_list = []
        for field_name, data_value in changed_data.items():
            field_dict = self._get_changed_field(field_name, data_value)
            if field_dict["old_value"] != field_dict["new_value"]:
                fields_list.append(field_dict)

        return sorted(fields_list, key=_key_by_notifiable_field)

    def get_watchers_to_notify(self, changer):
        watchers_to_notify = set()
        watchers_by_role = self._get_watchers_by_role()

        owner = watchers_by_role.get("owner", None)
        if (owner and owner.allow_notify_owned()
                and owner.allow_notify_by_me(changer)):
            watchers_to_notify.add(owner)

        assigned_to = watchers_by_role.get("assigned_to", None)
        if (assigned_to and assigned_to.allow_notify_assigned_to()
                and assigned_to.allow_notify_by_me(changer)):
            watchers_to_notify.add(assigned_to)

        suscribed_watchers = watchers_by_role.get("suscribed_watchers", None)
        if suscribed_watchers:
            for suscribed_watcher in suscribed_watchers:
                if (suscribed_watcher and suscribed_watcher.allow_notify_suscribed()
                        and suscribed_watcher.allow_notify_by_me(changer)):
                    watchers_to_notify.add(suscribed_watcher)

        (project, project_owner) = watchers_by_role.get("project_owner", (None, None))
        if (project_owner
                and project_owner.allow_notify_project(project)
                and project_owner.allow_notify_by_me(changer)):
            watchers_to_notify.add(project_owner)

        if changer.notify_changes_by_me:
            watchers_to_notify.add(changer)

        return watchers_to_notify

    def _get_changed_field_verbose_name(self, field_name):
        try:
            return self._meta.get_field(field_name).verbose_name
        except FieldDoesNotExist:
            return field_name

    def _get_changed_field_old_value(self, field_name, data_value):
        value = (self.last_version.field_dict.get(field_name, data_value)
                    if self.last_version else None)
        field = self.__class__._meta.get_field_by_name(field_name)[0] or None

        if value and field:
            # Get the old value from a ForeignKey
            if type(field) is models.fields.related.ForeignKey:
                try:
                    value = field.related.parent_model.objects.get(pk=value)
                except field.related.parent_model.DoesNotExist:
                    pass

        display_method = getattr(self,"get_notifiable_{field_name}_display".format(
                                                              field_name=field_name) ,None)
        return display_method(value) if display_method else value

    def _get_changed_field_new_value(self, field_name, data_value):
        value = getattr(self, field_name, data_value)
        display_method = getattr(self,"get_notifiable_{field_name}_display".format(
                                                              field_name=field_name) ,None)
        return display_method(value) if display_method else value

    def _get_changed_field(self, field_name, data_value):
        verbose_name = self._get_changed_field_verbose_name(field_name)
        old_value = self._get_changed_field_old_value(field_name, None)
        new_value = self._get_changed_field_new_value(field_name, data_value)

        return {
            "name": field_name,
            "verbose_name": verbose_name,
            "old_value": old_value,
            "new_value": new_value,
        }

    def _get_watchers_by_role(self):
        """
        Return the actual instances of watchers of this object, classified by role.
        For example:

           return {
               "owner": self.owner,
               "assigned_to": self.assigned_to,
               "suscribed_watchers": self.watchers.all(),
               "project_owner": (self.project, self.project.owner),
           }
        """
        raise NotImplementedError("You must subclass WatchedMixin and provide "
                                  "_get_watchers_by_role method")
