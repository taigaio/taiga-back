# -*- coding: utf-8 -*-

import random
import datetime

from sampledatahelper.helper import SampleDataHelper

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from django.contrib.webdesign import lorem_ipsum

from greenmine.base.users.models import *
from greenmine.projects.models import *
from greenmine.projects.milestones.models import *
from greenmine.projects.userstories.models import *
from greenmine.projects.tasks.models import *
from greenmine.projects.issues.models import *
from greenmine.projects.questions.models import *
from greenmine.projects.documents.models import *
from greenmine.projects.wiki.models import *


SUBJECT_CHOICES = [
    "Fixing templates for Django 1.2.",
    "get_actions() does not check for 'delete_selected' in actions",
    "Experimental: modular file types",
    "Add setting to allow regular users to create folders at the root level.",
    "add tests for bulk operations",
    "create testsuite with matrix builds",
    "Lighttpd support",
    "Lighttpd x-sendfile support",
    "Added file copying and processing of images (resizing)",
    "Exception is thrown if trying to add a folder with existing name",
    "Feature/improved image admin",
    "Support for bulk actions",
]


class Command(BaseCommand):
    sd = SampleDataHelper(seed=12345678901)

    @transaction.commit_on_success
    def handle(self, *args, **options):
        self.users = [User.objects.get(is_superuser=True)]
        for x in range(10):
            self.users.append(self.create_user(x))

        role = Role.objects.all()[0]

        # projects
        for x in range(3):
            project = self.create_project(x)

            for user in self.users:
                Membership.objects.create(project=project, role=role, user=user)

            start_date = now() - datetime.timedelta(35)

            # create random milestones
            for y in range(self.sd.int(1, 5)):
                end_date = start_date + datetime.timedelta(15)
                milestone = self.create_milestone(project, start_date, end_date)

                # create uss asociated to milestones
                for z in range(self.sd.int(3, 7)):
                    us = self.create_us(project, milestone)

                    for w in range(self.sd.int(0,6)):
                        if start_date <= now() and end_date <= now():
                            task = self.create_task(project, milestone, us, start_date, end_date, closed=True)
                        elif start_date <= now() and end_date >= now():
                            task = self.create_task(project, milestone, us, start_date, now())
                        else:
                            # No task on not initiated milestones
                            pass

                start_date = end_date

            # created unassociated uss.
            for y in range(self.sd.int(8,15)):
                us = self.create_us(project)

            # create bugs.
            for y in range(self.sd.int(15,25)):
                bug = self.create_bug(project)

            # create questions.
            #for y in range(self.sd.int(15,25)):
            #    question = self.create_question(project)

    def create_question(self, project):
        question = Question.objects.create(
            project=project,
            subject=self.sd.choice(SUBJECT_CHOICES),
            content=self.sd.paragraph(),
            owner=project.owner,
            status=self.sd.db_object_from_queryset(project.question_status.all()),
            tags=self.sd.words(1,5).split(" "),
        )

        return question

    def create_bug(self, project):
        bug = Issue.objects.create(
            project=project,
            subject=self.sd.choice(SUBJECT_CHOICES),
            description=self.sd.paragraph(),
            owner=project.owner,
            severity=self.sd.db_object_from_queryset(Severity.objects.filter(project=project)),
            status=self.sd.db_object_from_queryset(IssueStatus.objects.filter(project=project)),
            priority=self.sd.db_object_from_queryset(Priority.objects.filter(project=project)),
            type=self.sd.db_object_from_queryset(IssueType.objects.filter(project=project)),
            tags=self.sd.words(1, 5).split(" "),
        )

        return bug

    def create_task(self, project, milestone, us, min_date, max_date, closed=False):
        task = Task(
            subject=self.sd.choice(SUBJECT_CHOICES),
            description=self.sd.paragraph(),
            project=project,
            owner=self.sd.choice(self.users),
            milestone=milestone,
            user_story=us,
            finished_date=None,
        )
        if closed:
            task.status = project.task_statuses.get(order=4)
        else:
            task.status = self.sd.db_object_from_queryset(project.task_statuses.all())

        if task.status.is_closed:
            task.finished_date = self.sd.datetime_between(min_date, max_date)

        task.save()
        return task

    def create_us(self, project, milestone=None):
        us = UserStory.objects.create(
            subject=self.sd.choice(SUBJECT_CHOICES),
            project=project,
            owner=self.sd.choice(self.users),
            description=self.sd.paragraph(),
            milestone=milestone,
            status=self.sd.db_object_from_queryset(project.us_statuses.all()),
            tags=self.sd.words(1, 3).split(" ")
        )

        for role_points in us.role_points.all():
            if milestone:
                role_points.point = self.sd.db_object_from_queryset(
                               us.project.points.exclude(value=None))
            else:
                role_points.point = self.sd.db_object_from_queryset(
                                            us.project.points.all())

            role_points.save()

        return us

    def create_milestone(self, project, start_date, end_date):
        milestone = Milestone.objects.create(
            project=project,
            name='Sprint {0}-{1}-{2}'.format(start_date.year,
                                             start_date.month,
                                             start_date.day),
            owner=project.owner,
            created_date=start_date,
            modified_date=start_date,
            estimated_start=start_date,
            estimated_finish=end_date,
            order=10
        )
        return milestone

    def create_project(self, counter):
        # create project
        project = Project.objects.create(
            name='Project Example {0}'.format(counter),
            description='Project example {0} description'.format(counter),
            owner=random.choice(self.users),
            public=True,
            total_story_points=self.sd.int(100, 150),
            total_milestones=self.sd.int(5,10)
        )

        return project

    def create_user(self, counter):
        user = User.objects.create(
            username='user-{0}'.format(counter),
            first_name=self.sd.name('es'),
            last_name=self.sd.surname('es'),
            email=self.sd.email(),
            token=''.join(random.sample('abcdef0123456789', 10)),
        )

        user.set_password('user{0}'.format(counter))
        user.save()
        return user
