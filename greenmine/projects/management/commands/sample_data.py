# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from django.contrib.webdesign import lorem_ipsum
from django.contrib.contenttypes.models import ContentType

from sampledatahelper.helper import SampleDataHelper

from greenmine.base.users.models import *
from greenmine.projects.models import *
from greenmine.projects.milestones.models import *
from greenmine.projects.userstories.models import *
from greenmine.projects.tasks.models import *
from greenmine.projects.issues.models import *
#from greenmine.projects.questions.models import *
#from greenmine.projects.documents.models import *
from greenmine.projects.wiki.models import *

import random
import datetime

ATTACHMENT_SAMPLE_DATA = [
    "greenmine/projects/management/commands/sample_data",
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


class Command(BaseCommand):
    sd = SampleDataHelper(seed=12345678901)

    @transaction.atomic
    def handle(self, *args, **options):
        self.users = [User.objects.get(is_superuser=True)]

        # create users
        for x in range(10):
            self.users.append(self.create_user(x))

        # create project
        for x in range(4):
            project = self.create_project(x)

            # added memberships
            computable_project_roles = set()
            for user in self.users:
                role = self.sd.db_object_from_queryset(Role.objects.all())

                Membership.objects.create(
                        project=project,
                        role=role,
                        user=user)

                if role.computable:
                    computable_project_roles.add(role)

            start_date = now() - datetime.timedelta(55)

            # create milestones
            for y in range(self.sd.int(1, 5)):
                end_date = start_date + datetime.timedelta(15)
                milestone = self.create_milestone(project, start_date, end_date)

                # create uss asociated to milestones
                for z in range(self.sd.int(3, 7)):
                    us = self.create_us(project, milestone, computable_project_roles)

                    # create tasks
                    rang = (1, 4) if start_date <= now() and end_date <= now() else (0, 6)
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
            for y in range(self.sd.int(8,15)):
                us = self.create_us(project, None, computable_project_roles)

            # create bugs.
            for y in range(self.sd.int(15,25)):
                bug = self.create_bug(project)

            # create questions.
            #for y in range(self.sd.int(15,25)):
            #    question = self.create_question(project)

            # create a wiki page
            wiki_page = self.create_wiki(project, "home")

    def create_attachment(self, object):
        attachment = Attachment.objects.create(
                project=object.project,
                content_type=ContentType.objects.get_for_model(object.__class__),
                content_object=object,
                object_id=object.id,
                owner=self.sd.db_object_from_queryset(
                          object.project.memberships.all()).user,
                attached_file=self.sd.image_from_directory(*ATTACHMENT_SAMPLE_DATA))

        return attachment

    def create_wiki(self, project, slug):
        wiki_page = WikiPage.objects.create(
                project=project,
                slug=slug,
                content=self.sd.paragraphs(3,15),
                owner=self.sd.db_object_from_queryset(project.memberships.all()).user)

        for i in range(self.sd.int(0, 4)):
            attachment = self.create_attachment(wiki_page)

        return wiki_page

    #def create_question(self, project):
    #    question = Question.objects.create(
    #            project=project,
    #            subject=self.sd.choice(SUBJECT_CHOICES),
    #            content=self.sd.paragraph(),
    #            owner=self.sd.db_object_from_queryset(project.memberships.all()).user,
    #            status=self.sd.db_object_from_queryset(project.question_status.all()),
    #            tags=self.sd.words(1,5).split(" "))
    #
    #    for i in range(self.sd.int(0, 4)):
    #        attachment = self.create_attachment(question)
    #
    #    return question

    def create_bug(self, project):
        bug = Issue.objects.create(
                project=project,
                subject=self.sd.choice(SUBJECT_CHOICES),
                description=self.sd.paragraph(),
                owner=self.sd.db_object_from_queryset(project.memberships.all()).user,
                severity=self.sd.db_object_from_queryset(Severity.objects.filter(
                                                                  project=project)),
                status=self.sd.db_object_from_queryset(IssueStatus.objects.filter(
                                                                   project=project)),
                priority=self.sd.db_object_from_queryset(Priority.objects.filter(
                                                                  project=project)),
                type=self.sd.db_object_from_queryset(IssueType.objects.filter(
                                                               project=project)),
                tags=self.sd.words(1, 5).split(" "))

        for i in range(self.sd.int(0, 4)):
            attachment = self.create_attachment(bug)

        if bug.status.order != 1:
            bug.assigned_to = self.sd.db_object_from_queryset(project.memberships.all()).user
            bug.save()

        return bug

    def create_task(self, project, milestone, us, min_date, max_date, closed=False):
        task = Task(
                subject=self.sd.choice(SUBJECT_CHOICES),
                description=self.sd.paragraph(),
                project=project,
                owner=self.sd.db_object_from_queryset(project.memberships.all()).user,
                milestone=milestone,
                user_story=us,
                finished_date=None,
                assigned_to = self.sd.db_object_from_queryset(project.memberships.all()).user)

        if closed:
            task.status = project.task_statuses.get(order=4)
        else:
            task.status = self.sd.db_object_from_queryset(project.task_statuses.all())

        if task.status.is_closed:
            task.finished_date = self.sd.datetime_between(min_date, max_date)

        task.save()

        for i in range(self.sd.int(0, 4)):
            attachment = self.create_attachment(task)

        return task

    def create_us(self, project, milestone=None, computable_project_roles=list(Role.objects.all())):
        us = UserStory.objects.create(
                subject=self.sd.choice(SUBJECT_CHOICES),
                project=project,
                owner=self.sd.db_object_from_queryset(project.memberships.all()).user,
                description=self.sd.paragraph(),
                milestone=milestone,
                status=self.sd.db_object_from_queryset(project.us_statuses.filter(
                                                                   is_closed=False)),
                tags=self.sd.words(1, 3).split(" ")
        )

        for role_points in us.role_points.filter(role__in=computable_project_roles):
            if milestone:
                role_points.points = self.sd.db_object_from_queryset(
                                us.project.points.exclude(value=None))
            else:
                role_points.points = self.sd.db_object_from_queryset(
                                              us.project.points.all())

            role_points.save()

        for i in range(self.sd.int(0, 4)):
            attachment = self.create_attachment(us)

        return us

    def create_milestone(self, project, start_date, end_date):
        milestone = Milestone.objects.create(
                project=project,
                name='Sprint {0}-{1}-{2}'.format(start_date.year,
                                                 start_date.month,
                                                 start_date.day),
                owner=self.sd.db_object_from_queryset(project.memberships.all()).user,
                created_date=start_date,
                modified_date=start_date,
                estimated_start=start_date,
                estimated_finish=end_date,
                order=10)

        return milestone

    def create_project(self, counter):
        project = Project.objects.create(
                name='Project Example {0}'.format(counter),
                description='Project example {0} description'.format(counter),
                owner=random.choice(self.users),
                public=True,
                total_story_points=self.sd.int(600, 3000),
                total_milestones=self.sd.int(5,10))

        return project

    def create_user(self, counter):
        user = User.objects.create(
                username='user-{0}'.format(counter),
                first_name=self.sd.name('es'),
                last_name=self.sd.surname('es'),
                email=self.sd.email(),
                token=''.join(random.sample('abcdef0123456789', 10)),
                color=self.sd.choice(COLOR_CHOICES))

        user.set_password('user{0}'.format(counter))
        user.save()

        return user
