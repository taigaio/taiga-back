# -*- coding: utf-8 -*-

import random
import datetime

from sampledatahelper.helper import SampleDataHelper

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from django.contrib.webdesign import lorem_ipsum

from greenmine.base.users.models import User, Role
from greenmine.scrum.models import *
from greenmine.questions.models import *


subjects = [
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
        for x in xrange(3):
            project = self.create_project(x)

            for user in self.users:
                Membership.objects.create(project=project, role=role, user=user)

            start_date = now() - datetime.timedelta(35)

            # create random milestones
            for y in xrange(self.sd.int(1, 5)):
                end_date = start_date + datetime.timedelta(15)
                milestone = self.create_milestone(project, start_date, end_date)

                # create uss asociated to milestones
                for z in xrange(self.sd.int(3, 7)):
                    us = self.create_us(project, milestone)

                    for w in xrange(self.sd.int(0,6)):
                        if start_date <= now() and end_date <= now():
                            task = self.create_task(project, milestone, us, start_date, end_date, closed=True)
                        elif start_date <= now() and end_date >= now():
                            task = self.create_task(project, milestone, us, start_date, now())
                        else:
                            # No task on not initiated sprints
                            pass

                start_date = end_date

            # created unassociated uss.
            for y in xrange(self.sd.int(8,15)):
                us = self.create_us(project)

            # create bugs.
            for y in xrange(self.sd.int(15,25)):
                bug = self.create_bug(project)

            # create questions.
            #for y in xrange(self.sd.int(15,25)):
            #    question = self.create_question(project)

    def create_question(self, project):
        question = Question.objects.create(
            project=project,
            subject=self.sd.words(1,5),
            content=self.sd.paragraph(),
            owner=project.owner,
            status=self.sd.db_object_from_queryset(QuestionStatus.objects.filter(project=project)),
            tags=[],
        )

        for tag in self.sd.words(1,5).split(" "):
            question.tags.append(tag)

        question.save()

    def create_bug(self, project):
        bug = Issue.objects.create(
            project=project,
            subject=self.sd.words(1, 5),
            description=self.sd.paragraph(),
            owner=project.owner,
            severity=self.sd.db_object_from_queryset(Severity.objects.filter(project=project)),
            status=self.sd.db_object_from_queryset(IssueStatus.objects.filter(project=project)),
            priority=self.sd.db_object_from_queryset(Priority.objects.filter(project=project)),
            type=self.sd.db_object_from_queryset(IssueType.objects.filter(project=project)),
            tags=[],
        )

        for tag in self.sd.words(1, 5).split(" "):
            bug.tags.append(tag)

        bug.save()
        return bug

    def create_task(self, project, milestone, us, min_date, max_date, closed=False):
        task = Task(
            subject="Task {0}".format(self.sd.words(3,4)),
            description=self.sd.paragraph(),
            project=project,
            owner=self.sd.choice(self.users),
            milestone=milestone,
            user_story=us,
            finished_date=None,
        )
        if closed:
            task.status = TaskStatus.objects.get(project=project, order=4)
        else:
            task.status = self.sd.db_object_from_queryset(TaskStatus.objects.filter(project=project))

        if task.status.is_closed:
            task.finished_date = self.sd.datetime_between(min_date, max_date)

        task.save()
        return task

    def create_us(self, project, milestone=None):
        us = UserStory(
            subject=self.sd.words(4,9),
            project=project,
            owner=self.sd.choice(self.users),
            description=self.sd.paragraph(),
            milestone=milestone,
            status=self.sd.db_object_from_queryset(UserStoryStatus.objects.filter(project=project)),
            tags=[]
        )

        us.save()

        for role in project.list_roles:
            if milestone:
                points=self.sd.db_object_from_queryset(Points.objects.filter(project=project).exclude(order=0))
            else:
                points=self.sd.db_object_from_queryset(Points.objects.filter(project=project))

            RolePoints.objects.create(
                user_story=us,
                points=points,
                role=role)

        for tag in self.sd.words(1, 3).split(" "):
            us.tags.append(tag)

        us.save()
        return us

    def create_milestone(self, project, start_date, end_date):
        milestone = Milestone(
            project=project,
            name='Sprint {0}'.format(start_date),
            owner=project.owner,
            created_date=start_date,
            modified_date=start_date,
            estimated_start=start_date,
            estimated_finish=end_date,
            order=10
        )
        milestone.save()
        return milestone

    def create_project(self, counter):
        # create project
        project = Project(
            name='Project Example 1 {0}'.format(counter),
            description='Project example {0} description'.format(counter),
            owner=random.choice(self.users),
            public=True,
            total_story_points=self.sd.int(100, 150),
            sprints=self.sd.int(5,10)
        )

        project.save()
        return project

    def create_user(self, counter):
        user = User.objects.create(
            username='user-{0}-{1}'.format(counter, self.sd.word()),
            first_name=self.sd.name('es'),
            last_name=self.sd.surname('es'),
            email=self.sd.email(),
            token=''.join(random.sample('abcdef0123456789', 10)),
        )

        user.set_password('user{0}'.format(counter))
        user.save()
        return user
