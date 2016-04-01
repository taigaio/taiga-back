# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import random
import datetime
from os import path


from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from sampledatahelper.helper import SampleDataHelper

from taiga.users.models import *
from taiga.permissions.permissions import ANON_PERMISSIONS
from taiga.projects.choices import BLOCKED_BY_STAFF
from taiga.projects.models import *
from taiga.projects.milestones.models import *
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.services.stats import get_stats_for_project
from taiga.projects.userstories.models import *
from taiga.projects.tasks.models import *
from taiga.projects.issues.models import *
from taiga.projects.wiki.models import *
from taiga.projects.attachments.models import *
from taiga.projects.custom_attributes.models import *
from taiga.projects.custom_attributes.choices import TYPES_CHOICES, TEXT_TYPE, MULTILINE_TYPE, DATE_TYPE, URL_TYPE
from taiga.projects.history.services import take_snapshot
from taiga.projects.likes.services import add_like
from taiga.projects.votes.services import add_vote
from taiga.events.apps import disconnect_events_signals
from taiga.projects.services.stats import get_stats_for_project


ATTACHMENT_SAMPLE_DATA = [
    "taiga/projects/management/commands/sample_data",
    [".txt", ]
]

COLOR_CHOICES = [
    "#FC8EAC",
    "#A5694F",
    "#002e33",
    "#67CF00",
    "#71A6D2",
    "#FFF8E7",
    "#4B0082",
    "#007000",
    "#40826D",
    "#708090",
    "#761CEC",
    "#0F0F0F",
    "#D70A53",
    "#CC0000",
    "#FFCC00",
    "#FFFF00",
    "#C0FF33",
    "#B6DA55",
    "#2099DB"]


SUBJECT_CHOICES = [
    "Create the user model",
    "Implement the form",
    "Create the html template",
    "Fixing templates for Django 1.6.",
    "get_actions() does not check for 'delete_selected' in actions",
    "Experimental: modular file types",
    "Add setting to allow regular users to create folders at the root level.",
    "Add tests for bulk operations",
    "Create testsuite with matrix builds",
    "Lighttpd support",
    "Lighttpd x-sendfile support",
    "Added file copying and processing of images (resizing)",
    "Exception is thrown if trying to add a folder with existing name",
    "Feature/improved image admin",
    "Support for bulk actions",
    "Migrate to Python 3 and milk a beautiful cow"]

URL_CHOICES = [
    "https://taiga.io",
    "https://blog.taiga.io",
    "https://tree.taiga.io",
    "https://tribe.taiga.io"]

BASE_USERS = getattr(settings, "SAMPLE_DATA_BASE_USERS", {})
NUM_USERS = getattr(settings, "SAMPLE_DATA_NUM_USERS", 10)
NUM_INVITATIONS =getattr(settings, "SAMPLE_DATA_NUM_INVITATIONS",  2)
NUM_PROJECTS =getattr(settings, "SAMPLE_DATA_NUM_PROJECTS",  4)
NUM_EMPTY_PROJECTS = getattr(settings, "SAMPLE_DATA_NUM_EMPTY_PROJECTS", 2)
NUM_BLOCKED_PROJECTS = getattr(settings, "SAMPLE_DATA_NUM_BLOCKED_PROJECTS", 1)
NUM_MILESTONES = getattr(settings, "SAMPLE_DATA_NUM_MILESTONES", (1, 5))
NUM_USS = getattr(settings, "SAMPLE_DATA_NUM_USS", (3, 7))
NUM_TASKS_FINISHED = getattr(settings, "SAMPLE_DATA_NUM_TASKS_FINISHED", (1, 5))
NUM_TASKS = getattr(settings, "SAMPLE_DATA_NUM_TASKS", (0, 4))
NUM_USS_BACK = getattr(settings, "SAMPLE_DATA_NUM_USS_BACK", (8, 20))
NUM_ISSUES = getattr(settings, "SAMPLE_DATA_NUM_ISSUES", (12, 25))
NUM_ATTACHMENTS = getattr(settings, "SAMPLE_DATA_NUM_ATTACHMENTS", (0, 4))
NUM_LIKES = getattr(settings, "SAMPLE_DATA_NUM_LIKES", (0, 10))
NUM_VOTES = getattr(settings, "SAMPLE_DATA_NUM_VOTES", (0, 10))
NUM_WATCHERS = getattr(settings, "SAMPLE_DATA_NUM_PROJECT_WATCHERS", (0, 8))
FEATURED_PROJECTS_POSITIONS = [0, 1, 2]
LOOKING_FOR_PEOPLE_PROJECTS_POSITIONS = [0, 1, 2]


class Command(BaseCommand):
    sd = SampleDataHelper(seed=12345678901)

    @transaction.atomic
    def handle(self, *args, **options):
        # Prevent events emission when sample data is running
        disconnect_events_signals()

        self.users = [User.objects.get(is_superuser=True)]

        # create users
        if BASE_USERS:
            for username, full_name, email in BASE_USERS:
                self.users.append(self.create_user(username=username, full_name=full_name, email=email))
        else:
            for x in range(NUM_USERS):
                self.users.append(self.create_user(counter=x))

        # create project
        projects_range = range(NUM_PROJECTS + NUM_EMPTY_PROJECTS + NUM_BLOCKED_PROJECTS)
        empty_projects_range = range(NUM_PROJECTS, NUM_PROJECTS + NUM_EMPTY_PROJECTS )
        blocked_projects_range = range(
            NUM_PROJECTS + NUM_EMPTY_PROJECTS,
            NUM_PROJECTS + NUM_EMPTY_PROJECTS + NUM_BLOCKED_PROJECTS
        )

        for x in projects_range:
            project = self.create_project(
                x,
                is_private=(x in [2, 4] or self.sd.boolean()),
                blocked_code = BLOCKED_BY_STAFF if x in(blocked_projects_range) else None
            )

            # added memberships
            computable_project_roles = set()
            for user in self.users:
                if user == project.owner:
                    continue

                role = self.sd.db_object_from_queryset(project.roles.all())

                Membership.objects.create(email=user.email,
                                          project=project,
                                          role=role,
                                          is_admin=self.sd.boolean(),
                                          user=user)

                if role.computable:
                    computable_project_roles.add(role)

            # added invitations
            for i in range(NUM_INVITATIONS):
                role = self.sd.db_object_from_queryset(project.roles.all())

                Membership.objects.create(email=self.sd.email(),
                                          project=project,
                                          role=role,
                                          is_admin=self.sd.boolean(),
                                          token=''.join(random.sample('abcdef0123456789', 10)))

                if role.computable:
                    computable_project_roles.add(role)

            # added custom attributes
            if self.sd.boolean:
                for i in range(1, 4):
                    UserStoryCustomAttribute.objects.create(name=self.sd.words(1, 3),
                                                            description=self.sd.words(3, 12),
                                                            type=self.sd.choice(TYPES_CHOICES)[0],
                                                            project=project,
                                                            order=i)
            if self.sd.boolean:
                for i in range(1, 4):
                    TaskCustomAttribute.objects.create(name=self.sd.words(1, 3),
                                                       description=self.sd.words(3, 12),
                                                       type=self.sd.choice(TYPES_CHOICES)[0],
                                                       project=project,
                                                       order=i)
            if self.sd.boolean:
                for i in range(1, 4):
                    IssueCustomAttribute.objects.create(name=self.sd.words(1, 3),
                                                        description=self.sd.words(3, 12),
                                                        type=self.sd.choice(TYPES_CHOICES)[0],
                                                        project=project,
                                                        order=i)

            # If the project isn't empty
            if x not in empty_projects_range:
                start_date = now() - datetime.timedelta(55)

                # create milestones
                for y in range(self.sd.int(*NUM_MILESTONES)):
                    end_date = start_date + datetime.timedelta(15)
                    milestone = self.create_milestone(project, start_date, end_date)

                    # create uss asociated to milestones
                    for z in range(self.sd.int(*NUM_USS)):
                        us = self.create_us(project, milestone, computable_project_roles)

                        # create tasks
                        rang = NUM_TASKS_FINISHED if start_date <= now() and end_date <= now() else NUM_TASKS
                        for w in range(self.sd.int(*rang)):
                            if start_date <= now() and end_date <= now():
                                task = self.create_task(project, milestone, us, start_date,
                                                        end_date, closed=True)
                            elif start_date <= now() and end_date >= now():
                                task = self.create_task(project, milestone, us, start_date,
                                                        now())
                            else:
                                # No task on not initiated milestones
                                pass

                    start_date = end_date

                # created unassociated uss.
                for y in range(self.sd.int(*NUM_USS_BACK)):
                    us = self.create_us(project, None, computable_project_roles)

                # create bugs.
                for y in range(self.sd.int(*NUM_ISSUES)):
                    bug = self.create_bug(project)

                # create a wiki page
                wiki_page = self.create_wiki(project, "home")

            # Set a value to total_story_points to show the deadline in the backlog
            project_stats = get_stats_for_project(project)
            defined_points = project_stats["defined_points"]
            project.total_story_points = int(defined_points * self.sd.int(5,12) / 10)
            project.save()

            self.create_likes(project)


    def create_attachment(self, obj, order):
        attached_file = self.sd.file_from_directory(*ATTACHMENT_SAMPLE_DATA)
        membership = self.sd.db_object_from_queryset(obj.project.memberships
                                                     .filter(user__isnull=False))
        attachment = Attachment.objects.create(project=obj.project,
                                               name=path.basename(attached_file.name),
                                               size=attached_file.size,
                                               content_object=obj,
                                               order=order,
                                               owner=membership.user,
                                               is_deprecated=self.sd.boolean(),
                                               description=self.sd.words(3, 12),
                                               attached_file=attached_file)
        return attachment

    def create_wiki(self, project, slug):
        wiki_page = WikiPage.objects.create(project=project,
                                            slug=slug,
                                            content=self.sd.paragraphs(3,15),
                                            owner=self.sd.db_object_from_queryset(
                                                    project.memberships.filter(user__isnull=False)).user)

        for i in range(self.sd.int(*NUM_ATTACHMENTS)):
            attachment = self.create_attachment(wiki_page, i+1)

        take_snapshot(wiki_page,
                      comment=self.sd.paragraph(),
                      user=wiki_page.owner)

        # Add history entry
        wiki_page.content=self.sd.paragraphs(3,15)
        wiki_page.save()
        take_snapshot(wiki_page,
              comment=self.sd.paragraph(),
              user=wiki_page.owner)

        return wiki_page

    def get_custom_attributes_value(self, type):
        if type == TEXT_TYPE:
            return self.sd.words(1, 12)
        if type == MULTILINE_TYPE:
            return self.sd.paragraphs(2, 4)
        if type == DATE_TYPE:
            return self.sd.future_date(min_distance=0, max_distance=365)
        if type == URL_TYPE:
            return self.sd.choice(URL_CHOICES)
        return None

    def create_bug(self, project):
        bug = Issue.objects.create(project=project,
                                   subject=self.sd.choice(SUBJECT_CHOICES),
                                   description=self.sd.paragraph(),
                                   owner=self.sd.db_object_from_queryset(
                                            project.memberships.filter(user__isnull=False)).user,
                                   severity=self.sd.db_object_from_queryset(Severity.objects.filter(
                                                                                    project=project)),
                                   status=self.sd.db_object_from_queryset(IssueStatus.objects.filter(
                                                                                     project=project)),
                                   priority=self.sd.db_object_from_queryset(Priority.objects.filter(
                                                                                    project=project)),
                                   type=self.sd.db_object_from_queryset(IssueType.objects.filter(
                                                                                 project=project)),
                                   tags=self.sd.words(1, 10).split(" "))

        bug.save()

        custom_attributes_values = {str(ca.id): self.get_custom_attributes_value(ca.type) for ca
                                      in project.issuecustomattributes.all() if self.sd.boolean()}
        if custom_attributes_values:
            bug.custom_attributes_values.attributes_values = custom_attributes_values
            bug.custom_attributes_values.save()

        for i in range(self.sd.int(*NUM_ATTACHMENTS)):
            attachment = self.create_attachment(bug, i+1)

        if bug.status.order != 1:
            bug.assigned_to = self.sd.db_object_from_queryset(project.memberships.filter(
                                                                      user__isnull=False)).user
            bug.save()

        take_snapshot(bug,
                      comment=self.sd.paragraph(),
                      user=bug.owner)

        # Add history entry
        bug.status=self.sd.db_object_from_queryset(IssueStatus.objects.filter(project=project))
        bug.save()
        take_snapshot(bug,
              comment=self.sd.paragraph(),
              user=bug.owner)

        self.create_votes(bug)
        self.create_watchers(bug)

        return bug

    def create_task(self, project, milestone, us, min_date, max_date, closed=False):
        task = Task(subject=self.sd.choice(SUBJECT_CHOICES),
                    description=self.sd.paragraph(),
                    project=project,
                    owner=self.sd.db_object_from_queryset(project.memberships.filter(user__isnull=False)).user,
                    milestone=milestone,
                    user_story=us,
                    finished_date=None,
                    assigned_to = self.sd.db_object_from_queryset(
                    project.memberships.filter(user__isnull=False)).user,
                    tags=self.sd.words(1, 10).split(" "))

        if closed:
            task.status = project.task_statuses.get(order=4)
        else:
            task.status = self.sd.db_object_from_queryset(project.task_statuses.all())

        if task.status.is_closed:
            task.finished_date = self.sd.datetime_between(min_date, max_date)

        task.save()

        custom_attributes_values = {str(ca.id): self.get_custom_attributes_value(ca.type) for ca
                                       in project.taskcustomattributes.all() if self.sd.boolean()}
        if custom_attributes_values:
            task.custom_attributes_values.attributes_values = custom_attributes_values
            task.custom_attributes_values.save()

        for i in range(self.sd.int(*NUM_ATTACHMENTS)):
            attachment = self.create_attachment(task, i+1)

        take_snapshot(task,
                      comment=self.sd.paragraph(),
                      user=task.owner)

        # Add history entry
        task.status=self.sd.db_object_from_queryset(project.task_statuses.all())
        task.save()
        take_snapshot(task,
              comment=self.sd.paragraph(),
              user=task.owner)

        self.create_votes(task)
        self.create_watchers(task)

        return task

    def create_us(self, project, milestone=None, computable_project_roles=[]):
        us = UserStory.objects.create(subject=self.sd.choice(SUBJECT_CHOICES),
                                      project=project,
                                      owner=self.sd.db_object_from_queryset(
                                              project.memberships.filter(user__isnull=False)).user,
                                      description=self.sd.paragraph(),
                                      milestone=milestone,
                                      status=self.sd.db_object_from_queryset(project.us_statuses.filter(
                                                                             is_closed=False)),
                                      tags=self.sd.words(1, 3).split(" "))

        for role_points in us.role_points.filter(role__in=computable_project_roles):
            if milestone:
                role_points.points = self.sd.db_object_from_queryset(
                                us.project.points.exclude(value=None))
            else:
                role_points.points = self.sd.db_object_from_queryset(
                                              us.project.points.all())

            role_points.save()

        us.save()

        custom_attributes_values = {str(ca.id): self.get_custom_attributes_value(ca.type) for ca
                                 in project.userstorycustomattributes.all() if self.sd.boolean()}
        if custom_attributes_values:
            us.custom_attributes_values.attributes_values = custom_attributes_values
            us.custom_attributes_values.save()


        for i in range(self.sd.int(*NUM_ATTACHMENTS)):
            attachment = self.create_attachment(us, i+1)

        if self.sd.choice([True, True, False, True, True]):
            us.assigned_to = self.sd.db_object_from_queryset(project.memberships.filter(
                                                                     user__isnull=False)).user
            us.save()


        take_snapshot(us,
                      comment=self.sd.paragraph(),
                      user=us.owner)

        # Add history entry
        us.status=self.sd.db_object_from_queryset(project.us_statuses.filter(is_closed=False))
        us.save()
        take_snapshot(us,
              comment=self.sd.paragraph(),
              user=us.owner)

        self.create_votes(us)
        self.create_watchers(us)

        return us

    def create_milestone(self, project, start_date, end_date):
        milestone = Milestone.objects.create(project=project,
                                             name='Sprint {0}-{1}-{2}'.format(start_date.year,
                                                                              start_date.month,
                                                                              start_date.day),
                                              owner=self.sd.db_object_from_queryset(
                                                      project.memberships.filter(user__isnull=False)).user,
                                              created_date=start_date,
                                              modified_date=start_date,
                                              estimated_start=start_date,
                                              estimated_finish=end_date,
                                              order=10)
        take_snapshot(milestone, user=milestone.owner)

        return milestone

    def create_project(self, counter, is_private=None, blocked_code=None):
        if is_private is None:
            is_private=self.sd.boolean()

        anon_permissions = not is_private and list(map(lambda perm: perm[0], ANON_PERMISSIONS)) or []
        public_permissions = not is_private and list(map(lambda perm: perm[0], ANON_PERMISSIONS)) or []
        project = Project.objects.create(slug='project-%s'%(counter),
                                         name='Project Example {0}'.format(counter),
                                         description='Project example {0} description'.format(counter),
                                         owner=random.choice(self.users),
                                         is_private=is_private,
                                         anon_permissions=anon_permissions,
                                         public_permissions=public_permissions,
                                         total_story_points=self.sd.int(600, 3000),
                                         total_milestones=self.sd.int(5,10),
                                         tags=self.sd.words(1, 10).split(" "),
                                         is_looking_for_people=counter in LOOKING_FOR_PEOPLE_PROJECTS_POSITIONS,
                                         looking_for_people_note=self.sd.short_sentence(),
                                         is_featured=counter in FEATURED_PROJECTS_POSITIONS,
                                         blocked_code=blocked_code)

        project.is_kanban_activated = True
        project.save()
        take_snapshot(project, user=project.owner)

        self.create_likes(project)
        self.create_watchers(project, NotifyLevel.involved)

        return project

    def create_user(self, counter=None, username=None, full_name=None, email=None):
        counter = counter or self.sd.int()
        username = username or "user{0}".format(counter)
        full_name = full_name or "{} {}".format(self.sd.name('es'), self.sd.surname('es', number=1))
        email = email or "user{0}@taigaio.demo".format(counter)

        user = User.objects.create(username=username,
                                   full_name=full_name,
                                   email=email,
                                   token=''.join(random.sample('abcdef0123456789', 10)),
                                   color=self.sd.choice(COLOR_CHOICES))

        user.set_password('123123')
        user.save()

        return user

    def create_votes(self, obj):
        for i in range(self.sd.int(*NUM_VOTES)):
            user=self.sd.db_object_from_queryset(User.objects.all())
            add_vote(obj, user)

    def create_likes(self, obj):
        for i in range(self.sd.int(*NUM_LIKES)):
            user=self.sd.db_object_from_queryset(User.objects.all())
            add_like(obj, user)

    def create_watchers(self, obj, notify_level=None):
        for i in range(self.sd.int(*NUM_WATCHERS)):
            user = self.sd.db_object_from_queryset(User.objects.all())
            if not notify_level:
                obj.add_watcher(user)
            else:
                obj.add_watcher(user, notify_level)
