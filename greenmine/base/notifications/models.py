# -*- coding: utf-8 -*-

from django.db import models
from django.dispatch import Signal
from django.utils.translation import ugettext_lazy as _


watched_changed = Signal(providing_args = ['changed_attributes'])


class WatcherMixin(object):
    NOTIFY_LEVEL_CHOICES = (
        ('all_owned_projects', _(u'All events on my projects')),
        ('only_watching', _(u'Only events for objects i watch')),
        ('only_assigned', _(u'Only events for objects assigned to me')),
        ('only_owner', _(u'Only events for objects owned by me')),
        ('no_events', _(u'No events')),
    )

    notify_level = models.CharField(max_length=32, null=False, blank=False, default='only_watching',
                                    choices=NOTIFY_LEVEL_CHOICES, verbose_name=_(u'notify level'))
    notify_changes_by_me = models.BooleanField(null=False, blank=True,
                verbose_name=_(u'notify changes made by me'))

    class Meta:
        abstract = True

    def allow_notify_owned(self):
        return (self.notify_level in [
            'only_owner',
            'only_assigned',
            'only_watching',
            'all_owned_projects',
        ])

    def allow_notify_assigned_to(self):
        return (self.notify_level in [
            'only_assigned',
            'only_watching',
            'all_owned_projects',
        ])

    def allow_notify_suscribed(self):
        return (self.notify_level in [
            'only_watching',
            'all_owned_projects',
        ])

    def allow_notify_project(self, project):
        return self.notify_level == 'all_owned_projects' \
               and project.owner.pk == self.pk

    def allow_notify_by_me(self, changer):
        return (changer.pk != self.pk) \
               or self.notify_changes_by_me


class WatchedMixin(object):

    class Meta:
        abstract = True

    def start_change(self, changer):
        self._changer = changer
        self._saved_attributes = self._get_attributes_to_notify()

    def cancel_change(self):
        del self._changer
        del self._saved_attributes

    def complete_change(self):
        changed_attributes = self._get_changed_attributes()
        del self._changer
        del self._saved_attributes
        watched_changed.send(sender = self, changed_attributes = changed_attributes)

    def get_watchers_to_notify(self):
        watchers_to_notify = set()
        watchers_by_role = self._get_watchers_by_role()

        owner = watchers_by_role.get('owner')
        if owner \
           and owner.allow_notify_owned() \
           and owner.allow_notify_by_me(self._changer):
            watchers_to_notify.add(owner)

        assigned_to = watchers_by_role.get('assigned_to')
        if (assigned_to 
                and assigned_to.allow_notify_assigned_to()
                and assigned_to.allow_notify_by_me(self._changer)):
            watchers_to_notify.add(assigned_to)

        suscribed_watchers = watchers_by_role.get('suscribed_watchers')
        if suscribed_watchers:
            for suscribed_watcher in suscribed_watchers:
                if suscribed_watcher \
                   and suscribed_watcher.allow_notify_suscribed() \
                   and suscribed_watcher.allow_notify_by_me(self._changer):
                    watchers_to_notify.add(suscribed_watcher)

        #(project, project_owner) = watchers_by_role.get('project_owner')
        #if project_owner \
        #   and project_owner.allow_notify_project(project) \
        #   and project_owner.allow_notify_by_me(self._changer):
        #    watchers_to_notify.add(project_owner)

        return watchers_to_notify

    def _get_changed_attributes(self):
        changed_attributes = {}
        current_attributes = self._get_attributes_to_notify()
        for name, saved_value in self._saved_attributes.items():
            current_value = current_attributes.get(name)
            if saved_value != current_value:
                changed_attributes[name] = (saved_value, current_value)
        return changed_attributes

    def _get_watchers_by_role(self):
        '''
        Return the actual instances of watchers of this object, classified by role.
        For example:

           return {
               'owner': self.owner,
               'assigned_to': self.assigned_to,
               'suscribed_watchers': self.watchers.all(),
               'project_owner': (self.project, self.project.owner),
           }
        '''
        raise NotImplementedError('You must subclass WatchedMixin and provide _get_watchers_by_role method')

    def _get_attributes_to_notify(self):
        '''
        Return the names and values of the attributes of this object that will be checked for change in
        change notifications. Example:

          return {
              'name': self.name,
              'description': self.description,
              'status': self.status.name,
              ...
          }
        '''
        raise NotImplementedError('You must subclass WatchedMixin and provide _get_attributes_to_notify method')

