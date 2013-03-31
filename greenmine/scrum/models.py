# -*- coding: utf-8 -*-

from django.db import models

from django.utils import timezone
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import slugify_uniquely, ref_uniquely
from greenmine.base.fields import DictField
from greenmine.base.utils import iter_points
from greenmine.scrum.choices import *


class Severity(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)
    project = models.ForeignKey("Project", related_name="severities")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/severity({1})".format(self.project.id, self.name)


class IssueStatus(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)
    is_closed = models.BooleanField(default=False)
    project = models.ForeignKey("Project", related_name="issuestatuses")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/issue-status({1})".format(self.project.id, self.name)


class TaskStatus(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)
    is_closed = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default="#999999")
    project = models.ForeignKey("Project", related_name="taskstatuses")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/task-status({1})".format(self.project.id, self.name)


class UserStoryStatus(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)
    is_closed = models.BooleanField(default=False)
    project = models.ForeignKey("Project", related_name="usstatuses")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/us-status({1})".format(self.project.id, self.name)


class Priority(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)
    project = models.ForeignKey("Project", related_name="priorities")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/priority({1})".format(self.project.id, self.name)


class IssueType(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)

    project = models.ForeignKey("Project", related_name="issuetypes")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/type({1})".format(self.project.id, self.name)


class Points(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=10)

    project = models.ForeignKey("Project", related_name="points")

    class Meta:
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u"project({0})/point({1})".format(self.project.id, self.name)


class Project(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(blank=False)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True, auto_now=True)

    owner = models.ForeignKey("base.User", related_name="projects", blank=True)
    public = models.BooleanField(default=True)

    last_us_ref = models.BigIntegerField(null=True, default=1)
    last_task_ref = models.BigIntegerField(null=True, default=1)
    last_issue_ref = models.BigIntegerField(null=True, default=1)

    sprints = models.IntegerField(default=1, blank=True, null=True)
    total_story_points = models.FloatField(default=None, null=True)
    tags = PickledObjectField()

    class Meta:
        permissions = (
            # global permissions
            ('list_projects', 'Can list projects'),
            ('list_my_projects', 'Can list my projects'),

            # per project permissions
            ('view_projects', 'Can view projects'),

            ('create_tasks', 'Can create tasks'),
            ('comment_tasks', 'Can comment tasks'),
            ('modify_tasks', 'Can modify tasks'),
            ('delete_task', 'Can delete tasks'),
            ('modify_owned_tasks', 'Can modify owned tasks'),
            ('modify_assigned_tasks', 'Can modify assigned tasks'),
            ('assign_tasks_to_others', 'Can assign tasks to others'),
            ('assign_tasks_to_myself', 'Can assign tasks to myself'),
            ('change_tasks_state', 'Can change the task state'),
            ('add_tasks_to_us', 'Can add tasks to a user story'),

            ('create_us', 'Can create user stories'),
            ('comment_us', 'Can comment user stories'),
            ('modify_us', 'Can modify user stories'),
            ('delete_us', 'Can delete user stories'),
            ('modify_owned_us', 'Can modify owned user stories'),
            ('add_us_to_milestones', 'Can add user stories to milestones'),

            ('create_questions', 'Can create questions'),
            ('reply_questions', 'Can reply questions'),
            ('modify_questions', 'Can modify questions'),
            ('delete_questions', 'Can delete questions'),
            ('modify_owned_questions', 'Can modify owned questions'),

            ('create_wiki_page', 'Can create wiki pages'),
            ('modify_wiki_page', 'Can modify wiki pages'),
            ('delete_wiki_page', 'Can delete wiki pages'),
            ('modify_owned_wiki_page', 'Can modify owned wiki pages'),

            ('create_documents', 'Can create documents'),
            ('modify_documents', 'Can modify documents'),
            ('delete_documents', 'Can delete documents'),
            ('modify_owned_documents', 'Can modify owned documents'),

            ('create_milestone', 'Can create milestones'),
            ('modify_milestone', 'Can modify milestones'),

            ('manage_users', 'Can manage users'),
        )

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<Project %s>" % (self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Project, self).save(*args, **kwargs)


class Milestone(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    owner = models.ForeignKey('base.User', related_name="milestones",
                              null=True, blank=True)
    project = models.ForeignKey('Project', related_name="milestones")

    estimated_start = models.DateField(null=True, default=None)
    estimated_finish = models.DateField(null=True, default=None)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True, auto_now=True)
    closed = models.BooleanField(default=False)

    disponibility = models.FloatField(null=True, default=0.0)
    order = models.PositiveSmallIntegerField("Order", default=1)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Milestone, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-created_date']
        unique_together = ('name', 'project')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<Milestone %s>" % (self.id)


class UserStory(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    ref = models.BigIntegerField(db_index=True, null=True, default=None, blank=True)
    milestone = models.ForeignKey("Milestone", blank=True,
                                  related_name="user_stories", null=True,
                                  default=None)
    project = models.ForeignKey("Project", related_name="user_stories")
    owner = models.ForeignKey("base.User", blank=True, null=True,
                              related_name="user_stories")

    status = models.ForeignKey("UserStoryStatus", related_name="userstories")
    points = models.ForeignKey("Points", related_name="userstories")
    order = models.PositiveSmallIntegerField(default=100)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True, auto_now=True)
    finish_date = models.DateTimeField(null=True, blank=True)

    subject = models.CharField(max_length=500)
    description = models.TextField()

    watchers = models.ManyToManyField('base.User', related_name='us_watch', null=True)

    client_requirement = models.BooleanField(default=False)
    team_requirement = models.BooleanField(default=False)
    tags = PickledObjectField()

    class Meta:
        ordering = ['order']
        unique_together = ('ref', 'project')

    def __repr__(self):
        return u"<UserStory %s>" % (self.id)

    def __unicode__(self):
        return u"{0} ({1})".format(self.subject, self.ref)

    @property
    def is_closed(self):
        return self.status.is_closed


class Change(models.Model):
    change_type = models.IntegerField(choices=TASK_CHANGE_CHOICES)
    owner = models.ForeignKey('base.User', related_name='changes')
    created_date = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey("Project", related_name="changes")

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    data = PickledObjectField()
    tags = PickledObjectField()


class ChangeAttachment(models.Model):
    change = models.ForeignKey("Change", related_name="attachments")
    owner = models.ForeignKey("base.User", related_name="change_attachments")

    created_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/msg", max_length=500,
                                     null=True, blank=True)
    tags = PickledObjectField()


class Task(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    user_story = models.ForeignKey('UserStory', related_name='tasks')
    ref = models.BigIntegerField(db_index=True, null=True, default=None)
    owner = models.ForeignKey("base.User", null=True, default=None,
                              related_name="tasks")

    status = models.ForeignKey("TaskStatus", related_name="tasks")
    severity = models.ForeignKey("Severity", related_name="tasks")
    priority = models.ForeignKey("Priority", related_name="tasks")
    status = models.ForeignKey("TaskStatus", related_name="tasks")

    milestone = models.ForeignKey('Milestone', related_name='tasks', null=True,
                                  default=None, blank=True)

    project = models.ForeignKey('Project', related_name='tasks')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    finished_date = models.DateTimeField(null=True, blank=True)

    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey('base.User',
                                    related_name='user_storys_assigned_to_me',
                                    blank=True, null=True, default=None)

    watchers = models.ManyToManyField('base.User', related_name='task_watch',
                                      null=True)

    changes = generic.GenericRelation(Change)
    tags = PickledObjectField()

    class Meta:
        unique_together = ('ref', 'project')

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, "last_task_ref", self.__class__)

        super(Task, self).save(*args, **kwargs)


class Issue(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    ref = models.BigIntegerField(db_index=True, null=True, default=None)
    owner = models.ForeignKey("base.User", null=True, default=None,
                              related_name="issues")

    status = models.ForeignKey("IssueStatus", related_name="issues")
    severity = models.ForeignKey("Severity", related_name="issues")
    priority = models.ForeignKey("Priority", related_name="issues")
    type = models.ForeignKey("IssueType", related_name="issues")

    milestone = models.ForeignKey('Milestone', related_name='issues', null=True,
                                  default=None, blank=True)

    project = models.ForeignKey('Project', related_name='issues')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    finished_date = models.DateTimeField(null=True, blank=True)

    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey('base.User',
                                    related_name='issues_assigned_to_me',
                                    blank=True, null=True, default=None)

    watchers = models.ManyToManyField('base.User', related_name='issue_watch',
                                      null=True)

    changes = generic.GenericRelation(Change)
    tags = PickledObjectField()

    class Meta:
        unique_together = ('ref', 'project')

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, "last_issue_ref", self.__class__)

        super(Issue, self).save(*args, **kwargs)


# Model related signals handlers

@receiver(models.signals.post_save, sender=Project, dispatch_uid="project_post_save")
def project_post_save(sender, instance, created, **kwargs):
    """
    Create all project model depences on project is
    created.
    """

    from greenmine.base.services import RoleGroupsService

    if not created:
        return

    RoleGroupsService().replicate_all_roles_on_one_project(instance)

    # Populate new project dependen default data

    for order, name, is_closed in ISSUESTATUSES:
        IssueStatus.objects.create(name=name, order=order,
                                    is_closed=is_closed, project=instance)

    for order, name, is_closed, color in TASKSTATUSES:
        TaskStatus.objects.create(name=name, order=order, color=color,
                                    is_closed=is_closed, project=instance)

    for order, name, is_closed in USSTATUSES:
        UserStoryStatus.objects.create(name=name, order=order,
                                    is_closed=is_closed, project=instance)

    for order, name in POINTS_CHOICES:
        Priority.objects.create(project=instance, name=name, order=order)

    for order, name in SEVERITY_CHOICES:
        Severity.objects.create(project=instance, name=name, order=order)

    for order, name in POINTS_CHOICES:
        Points.objects.create(project=instance, name=name, order=order)

    for order, name in ISSUETYPES:
        IssueType.objects.create(project=instance, name=name, order=order)


@receiver(models.signals.pre_save, sender=UserStory, dispatch_uid="user_story_ref_handler")
def user_story_ref_handler(sender, instance, **kwargs):
    """
    Automatically assignes a seguent reference code to a
    user story if that is not created.
    """

    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_us_ref", instance.__class__)


# Email alerts signals handlers
# TODO: temporary commented (Pending refactor)
# from . import sigdispatch
