# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.db.models.loading import get_model
from django.db.models import signals
from django.dispatch import receiver

from taiga.timeline.service import push_to_timeline

# TODO: Add events to followers timeline when followers are implemented.
# TODO: Add events to project watchers timeline when project watchers are implemented.


@receiver(signals.post_save, sender=get_model("projects", "Project"))
def create_project_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        push_to_timeline(instance, instance, "create")


@receiver(signals.post_save, sender=get_model("userstories", "UserStory"))
def create_user_story_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        push_to_timeline(instance.project, instance, "create")


@receiver(signals.post_save, sender=get_model("issues", "Issue"))
def create_issue_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        push_to_timeline(instance.project, instance, "create")


@receiver(signals.pre_save, sender=get_model("projects", "Membership"))
def create_membership_push_to_timeline(sender, instance, **kwargs):
    if not instance.pk and instance.user:
        push_to_timeline(instance.project, instance, "create")
    elif instance.pk:
        prev_instance = sender.objects.get(pk=instance.pk)
        if prev_instance.user != prev_instance.user:
            push_to_timeline(instance.project, instance, "create")
        elif prev_instance.role != prev_instance.role:
            extra_data = {
                "prev_role": {
                    "id": prev_instance.role.pk,
                    "name": prev_instance.role.name,
                }
            }
            push_to_timeline(instance.project, instance, "role-changed", extra_data=extra_data)


@receiver(signals.post_delete, sender=get_model("projects", "Membership"))
def delete_membership_push_to_timeline(sender, instance, **kwargs):
    push_to_timeline(instance.project, instance, "delete")
