# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import slugify_uniquely, ref_uniquely
from greenmine.base.utils import iter_points
from greenmine.base.notifications.models import WatchedMixin
from greenmine.scrum.choices import (ISSUESTATUSES, TASKSTATUSES, USSTATUSES,
                                     POINTS_CHOICES, SEVERITY_CHOICES,
                                     ISSUETYPES, TASK_CHANGE_CHOICES,
                                     PRIORITY_CHOICES)


class Severity(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='severities',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'severity'
        verbose_name_plural = u'severities'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class IssueStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is closed'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='issue_statuses',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'issue status'
        verbose_name_plural = u'issue statuses'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class TaskStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is closed'))
    color = models.CharField(max_length=20, null=False, blank=False, default='#999999',
                verbose_name=_('color'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='task_statuses',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'task status'
        verbose_name_plural = u'task statuses'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class UserStoryStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is closed'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='us_statuses',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'user story status'
        verbose_name_plural = u'user story statuses'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class Priority(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='priorities',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'priority'
        verbose_name_plural = u'priorities'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class IssueType(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='issue_types',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'issue type'
        verbose_name_plural = u'issue types'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class Points(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                verbose_name=_('name'))
    order = models.IntegerField(default=10, null=False, blank=False,
                verbose_name=_('order'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='points',
                verbose_name=_('project'))

    class Meta:
        verbose_name = u'point'
        verbose_name_plural = u'points'
        ordering = ['project', 'name']
        unique_together = ('project', 'name')

    def __unicode__(self):
        return u'project {0} - {1}'.format(self.project_id, self.name)


class Membership(models.Model):
    user = models.ForeignKey('base.User', null=False, blank=False)
    project = models.ForeignKey('Project', null=False, blank=False)
    role = models.ForeignKey('base.Role', null=False, blank=False)

    class Meta:
        unique_together = ('user', 'project')


class Project(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                verbose_name=_('uuid'))
    name = models.CharField(max_length=250, unique=True, null=False, blank=False,
                verbose_name=_('name'))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                verbose_name=_('slug'))
    description = models.TextField(null=False, blank=False,
                verbose_name=_('description'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    owner = models.ForeignKey('base.User', null=False, blank=True,
                related_name='owned_projects',
                verbose_name=_('owner'))
    members = models.ManyToManyField('base.User', related_name='projects', through='Membership',
                verbose_name=_('members'))
    public = models.BooleanField(default=True, null=False, blank=True,
                verbose_name=_('public'))
    last_us_ref = models.BigIntegerField(null=True, blank=False, default=1,
                verbose_name=_('last us ref'))
    last_task_ref = models.BigIntegerField(null=True, blank=False, default=1,
                verbose_name=_('last task ref'))
    last_issue_ref = models.BigIntegerField(null=True, blank=False, default=1,
                verbose_name=_('last issue ref'))
    sprints = models.IntegerField(default=1, null=True, blank=True,
                verbose_name=_('number of sprints'))
    total_story_points = models.FloatField(default=None, null=True, blank=False,
                verbose_name=_('total story points'))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'project'
        verbose_name_plural = u'projects'
        ordering = ['name']
        permissions = (
            ('can_list_projects', 'Can list projects'),
            ('can_view_project', 'Can view project'),
            ('can_manage_users', 'Can manage users'),
        )

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u'<Project {0}>'.format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Project, self).save(*args, **kwargs)

    def _get_watchers_by_role(self):
        return {
            'owner': self.owner,
        }

    def _get_attributes_to_notify(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'modified_date': self.modified_date,
            'owner': self.owner.get_full_name(),
            'members': ', '.join([member.get_full_name() for member in self.members.all()]),
            'public': self.public,
            'tags': self.tags,
        }


class Milestone(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                verbose_name=_('uuid'))
    name = models.CharField(max_length=200, db_index=True, null=False, blank=False,
                verbose_name=_('name'))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                verbose_name=_('slug'))
    owner = models.ForeignKey('base.User', null=True, blank=False,
                related_name='owned_milestones',
                verbose_name=_('owner'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='milestones',
                verbose_name=_('project'))
    estimated_start = models.DateField(null=True, blank=True, default=None,
                verbose_name=_('estimated start'))
    estimated_finish = models.DateField(null=True, blank=True, default=None,
                verbose_name=_('estimated finish'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    closed = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is closed'))
    disponibility = models.FloatField(default=0.0, null=True, blank=True,
                verbose_name=_('disponibility'))
    order = models.PositiveSmallIntegerField(default=1, null=False, blank=False,
                verbose_name=_('order'))

    class Meta:
        verbose_name = u'milestone'
        verbose_name_plural = u'milestones'
        ordering = ['project', '-created_date']
        unique_together = ('name', 'project')
        permissions = (
            ('can_view_milestone', 'Can view milestones'),
        )

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u'<Milestone {0}>'.format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Milestone, self).save(*args, **kwargs)

    def _get_watchers_by_role(self):
        return {
            'owner': self.owner,
            'project_owner': (self.project, self.project.owner),
        }

    def _get_attributes_to_notify(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'owner': self.owner.get_full_name(),
            'modified_date': self.modified_date,
        }


class UserStory(WatchedMixin, models.Model):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                verbose_name=_('uuid'))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                verbose_name=_('ref'))
    milestone = models.ForeignKey('Milestone', null=True, blank=True, default=None,
                related_name='user_stories',
                verbose_name=_('milestone'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='user_stories',
                verbose_name=_('project'))
    owner = models.ForeignKey('base.User', null=True, blank=True,
                related_name='owned_user_stories',
                verbose_name=_('owner'))
    status = models.ForeignKey('UserStoryStatus', null=False, blank=False,
                related_name='user_stories',
                verbose_name=_('status'))
    points = models.ForeignKey('Points', null=False, blank=False,
                related_name='userstories',
                verbose_name=_('points'))
    order = models.PositiveSmallIntegerField(null=False, blank=False, default=100,
                verbose_name=_('order'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    finish_date = models.DateTimeField(null=True, blank=True,
                verbose_name=_('finish date'))
    subject = models.CharField(max_length=500, null=False, blank=False,
                verbose_name=_('subject'))
    description = models.TextField(null=False, blank=True,
                verbose_name=_('description'))
    watchers = models.ManyToManyField('base.User', null=True, blank=True,
                related_name='watched_us',
                verbose_name=_('watchers'))
    client_requirement = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is client requirement'))
    team_requirement = models.BooleanField(default=False, null=False, blank=True,
                verbose_name=_('is team requirement'))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'user story'
        verbose_name_plural = u'user stories'
        ordering = ['project', 'order']
        unique_together = ('ref', 'project')
        permissions = (
            ('can_comment_userstory', 'Can comment user stories'),
            ('can_view_userstory', 'Can view user stories'),
            ('can_change_owned_userstory', 'Can modify owned user stories'),
            ('can_delete_userstory', 'Can delete user stories'),
            ('can_add_userstory_to_milestones', 'Can add user stories to milestones'),
        )

    def __unicode__(self):
        return u'({1}) {0}'.format(self.ref, self.subject)

    def __repr__(self):
        return u'<UserStory %s>' % (self.id)

    @property
    def is_closed(self):
        return self.status.is_closed

    def _get_watchers_by_role(self):
        return {
            'owner': self.owner,
            'suscribed_watchers': self.watchers.all(),
            'project_owner': (self.project, self.project.owner),
        }

    def _get_attributes_to_notify(self):
        return {
            'milestone': self.milestone.name,
            'owner': self.owner.get_full_name(),
            'status': self.status.name,
            'points': self.points.name,
            'order': self.order,
            'modified_date': self.modified_date,
            'finish_date': self.finish_date,
            'subject': self.subject,
            'description': self.description,
            'client_requirement': self.client_requirement,
            'team_requirement': self.team_requirement,
            'tags': self.tags,
        }


class Attachment(models.Model):
    owner = models.ForeignKey('base.User', null=False, blank=False,
                related_name='change_attachments',
                verbose_name=_('owner'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='attachments',
                verbose_name=_('project'))
    content_type = models.ForeignKey(ContentType, null=False, blank=False,
                verbose_name=_('content type'))
    object_id = models.PositiveIntegerField(null=False, blank=False,
                verbose_name=_('object id'))
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                verbose_name=_('modified date'))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                upload_to='files/msg',
                verbose_name=_('attached file'))

    class Meta:
        verbose_name = u'attachment'
        verbose_name_plural = u'attachments'
        ordering = ['project', 'created_date']

    def __unicode__(self):
        return u'content_type {0} - object_id {1} - attachment {2}'.format(
                self.content_type, self.object_id, self.id
        )


class Task(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                verbose_name=_('uuid'))
    user_story = models.ForeignKey('UserStory', null=False, blank=False,
                related_name='tasks',
                verbose_name=_('user story'))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                verbose_name=_('ref'))
    owner = models.ForeignKey('base.User', null=True, blank=True, default=None,
                related_name='owned_tasks',
                verbose_name=_('owner'))
    severity = models.ForeignKey('Severity', null=False, blank=False,
                related_name='tasks',
                verbose_name=_('severity'))
    priority = models.ForeignKey('Priority', null=False, blank=False,
                related_name='tasks',
                verbose_name=_('priority'))
    status = models.ForeignKey('TaskStatus', null=False, blank=False,
                related_name='tasks',
                verbose_name=_('status'))
    milestone = models.ForeignKey('Milestone', null=True, blank=True, default=None,
                related_name='tasks',
                verbose_name=_('milestone'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='tasks',
                verbose_name=_('project'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('modified date'))
    finished_date = models.DateTimeField(null=True, blank=True,
                verbose_name=_('finished date'))
    subject = models.CharField(max_length=500, null=False, blank=False,
                verbose_name=_('subject'))
    description = models.TextField(null=False, blank=True,
                verbose_name=_('description'))
    assigned_to = models.ForeignKey('base.User', blank=True, null=True, default=None,
                related_name='user_storys_assigned_to_me',
                verbose_name=_('assigned to'))
    watchers = models.ManyToManyField('base.User', null=True, blank=True,
                related_name='watched_tasks',
                verbose_name=_('watchers'))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'task'
        verbose_name_plural = u'tasks'
        ordering = ['project', 'created_date']
        unique_together = ('ref', 'project')
        permissions = (
            ('can_comment_task', 'Can comment tasks'),
            ('can_change_owned_task', 'Can modify owned tasks'),
            ('can_change_assigned_task', 'Can modify assigned tasks'),
            ('can_assign_task_to_other', 'Can assign tasks to others'),
            ('can_assign_task_to_myself', 'Can assign tasks to myself'),
            ('can_change_task_state', 'Can change the task state'),
            ('can_view_task', 'Can view the task'),
            ('can_add_task_to_us', 'Can add tasks to a user story'),
        )

    def __unicode__(self):
        return u'({1}) {0}'.format(self.ref, self.subject)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, 'last_task_ref', self.__class__)

        super(Task, self).save(*args, **kwargs)

    def _get_watchers_by_role(self):
        return {
            'owner': self.owner,
            'assigned_to': self.assigned_to,
            'suscribed_watchers': self.watchers.all(),
            'project_owner': (self.project, self.project.owner),
        }


class Issue(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                verbose_name=_('uuid'))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                verbose_name=_('ref'))
    owner = models.ForeignKey('base.User', null=True, blank=True, default=None,
                related_name='owned_issues',
                verbose_name=_('owner'))
    status = models.ForeignKey('IssueStatus', null=False, blank=False,
                related_name='issues',
                verbose_name=_('status'))
    severity = models.ForeignKey('Severity', null=False, blank=False,
                related_name='issues',
                verbose_name=_('severity'))
    priority = models.ForeignKey('Priority', null=False, blank=False,
                related_name='issues',
                verbose_name=_('priority'))
    type = models.ForeignKey('IssueType', null=False, blank=False,
                related_name='issues',
                verbose_name=_('type'))
    milestone = models.ForeignKey('Milestone', null=True, blank=True, default=None,
                related_name='issues',
                verbose_name=_('milestone'))
    project = models.ForeignKey('Project', null=False, blank=False,
                related_name='issues',
                verbose_name=_('project'))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('created date'))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                verbose_name=_('modified date'))
    finished_date = models.DateTimeField(null=True, blank=True,
                verbose_name=_('finished date'))
    subject = models.CharField(max_length=500, null=False, blank=False,
                verbose_name=_('subject'))
    description = models.TextField(null=False, blank=True,
                verbose_name=_('description'))
    assigned_to = models.ForeignKey('base.User', blank=True, null=True, default=None,
                related_name='issues_assigned_to_me',
                verbose_name=_('assigned to'))
    watchers = models.ManyToManyField('base.User', null=True, blank=True,
                related_name='watched_issues',
                verbose_name=_('watchers'))
    tags = PickledObjectField(null=False, blank=True,
                verbose_name=_('tags'))

    class Meta:
        verbose_name = u'issue'
        verbose_name_plural = u'issues'
        ordering = ['project', 'created_date']
        unique_together = ('ref', 'project')
        permissions = (
            ('can_comment_issue', 'Can comment issues'),
            ('can_change_owned_issue', 'Can modify owned issues'),
            ('can_change_assigned_issue', 'Can modify assigned issues'),
            ('can_assign_issue_to_other', 'Can assign issues to others'),
            ('can_assign_issue_to_myself', 'Can assign issues to myself'),
            ('can_change_issue_state', 'Can change the issue state'),
            ('can_view_issue', 'Can view the issue'),
        )

    def __unicode__(self):
        return u'({1}) {0}'.format(self.ref, self.subject)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        if not self.ref:
            self.ref = ref_uniquely(self.project, 'last_issue_ref', self.__class__)

        super(Issue, self).save(*args, **kwargs)

    def _get_watchers_by_role(self):
        return {
            'owner': self.owner,
            'assigned_to': self.assigned_to,
            'suscribed_watchers': self.watchers.all(),
            'project_owner': (self.project, self.project.owner),
        }


# Model related signals handlers

@receiver(models.signals.post_save, sender=Project, dispatch_uid='project_post_save')
def project_post_save(sender, instance, created, **kwargs):
    """
    Create all project model depences on project is
    created.
    """

    if not created:
        return

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

    for order, name in PRIORITY_CHOICES:
        Priority.objects.create(project=instance, name=name, order=order)

    for order, name in SEVERITY_CHOICES:
        Severity.objects.create(project=instance, name=name, order=order)

    for order, name in POINTS_CHOICES:
        Points.objects.create(project=instance, name=name, order=order)

    for order, name in ISSUETYPES:
        IssueType.objects.create(project=instance, name=name, order=order)


@receiver(models.signals.pre_save, sender=UserStory, dispatch_uid='user_story_ref_handler')
def user_story_ref_handler(sender, instance, **kwargs):
    """
    Automatically assignes a seguent reference code to a
    user story if that is not created.
    """

    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, 'last_us_ref', instance.__class__)


# Email alerts signals handlers
# TODO: temporary commented (Pending refactor)
# from . import sigdispatch
