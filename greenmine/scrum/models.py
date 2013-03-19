# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.contrib.auth.models import UserManager

from greenmine.core.utils.slug import slugify_uniquely, ref_uniquely
from greenmine.core.fields import DictField, ListField
from greenmine.wiki.fields import WikiField
from greenmine.core.utils import iter_points
from greenmine.taggit.managers import TaggableManager
import reversion

from .choices import *

import datetime
import re

from .utils import SCRUM_STATES

class ProjectManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def can_view(self, user):
        queryset = ProjectUserRole.objects.filter(user=user)\
            .values_list('project', flat=True)
        return Project.objects.filter(pk__in=queryset)


class ProjectExtras(models.Model):
    task_parser_re = models.CharField(max_length=1000, blank=True, null=True, default=None)
    sprints = models.IntegerField(default=1, blank=True, null=True)
    show_burndown = models.BooleanField(default=False, blank=True)
    show_burnup = models.BooleanField(default=False, blank=True)
    show_sprint_burndown = models.BooleanField(default=False, blank=True)
    total_story_points = models.FloatField(default=None, null=True)

    def get_task_parse_re(self):
        re_str = settings.DEFAULT_TASK_PARSER_RE
        if self.task_parser_re:
            re_str = self.task_parser_re
        return re.compile(re_str, flags=re.U+re.M)

    def parse_ustext(self, text):
        rx = self.get_task_parse_re()
        texts = rx.findall(text)
        for text in texts:
            yield text


class Project(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = WikiField(blank=False)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey("auth.User", related_name="projects")
    participants = models.ManyToManyField('auth.User',
        related_name="projects_participant", through="ProjectUserRole",
        null=True, blank=True)

    public = models.BooleanField(default=True)
    markup = models.CharField(max_length=10, choices=MARKUP_TYPE, default='md')
    extras = models.OneToOneField("ProjectExtras", related_name="project", null=True, default=None)

    last_us_ref = models.BigIntegerField(null=True, default=0)
    last_task_ref = models.BigIntegerField(null=True, default=0)

    objects = ProjectManager()

    def __unicode__(self):
        return self.name

    def get_extras(self):
        if self.extras is None:
            self.extras = ProjectExtras.objects.create()
            self.__class__.objects.filter(pk=self.pk).update(extras=self.extras)

        return self.extras

    def natural_key(self):
        return (self.slug,)

    @property
    def unasociated_user_stories(self):
        return self.user_stories.filter(milestone__isnull=True)

    @property
    def all_participants(self):
        qs = ProjectUserRole.objects.filter(project=self)
        return User.objects.filter(id__in=qs.values_list('user__pk', flat=True))

    @property
    def default_milestone(self):
        return self.milestones.order_by('-created_date')[0]

    def __repr__(self):
        return u"<Project %s>" % (self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)
        else:
            self.modified_date = timezone.now()

        super(Project, self).save(*args, **kwargs)

    def add_user(self, user, role):
        from greenmine.core import permissions
        return ProjectUserRole.objects.create(
            project = self,
            user = user,
            role = permissions.get_role(role),
        )


    """ Permalinks """
    @models.permalink
    def get_absolute_url(self):
        return ('project-backlog', (),
            {'pslug': self.slug})

    @models.permalink
    def get_dashboard_url(self):
        return ('dashboard', (), {'pslug': self.slug})

    @models.permalink
    def get_backlog_url(self):
        return ('project-backlog', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_stats_url(self):
        return ('project-backlog-stats', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_left_block_url(self):
        return ('project-backlog-left-block', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_right_block_url(self):
        return ('project-backlog-right-block', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_burndown_url(self):
        return ('project-backlog-burndown', (),
            {'pslug': self.slug})

    @models.permalink
    def get_backlog_burnup_url(self):
        return ('project-backlog-burnup', (),
            {'pslug': self.slug})

    @models.permalink
    def get_milestone_create_url(self):
        return ('milestone-create', (),
            {'pslug': self.slug})

    @models.permalink
    def get_userstory_create_url(self):
        return ('user-story-create', (), {'pslug': self.slug})

    @models.permalink
    def get_edit_url(self):
        return ('project-edit', (), {'pslug': self.slug})

    @models.permalink
    def get_delete_url(self):
        return ('project-delete', (), {'pslug': self.slug})

    @models.permalink
    def get_export_url(self):
        return ('project-export-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_export_now_url(self):
        return ('project-export-settings-now', (), {'pslug': self.slug})

    @models.permalink
    def get_export_rehash_url(self):
        return ('project-export-settings-rehash', (), {'pslug': self.slug})

    @models.permalink
    def get_issues_url(self):
        return ('issues-list', (), {'pslug': self.slug})

    @models.permalink
    def get_settings_url(self):
        return ('project-personal-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_general_settings_url(self):
        return ('project-general-settings', (), {'pslug': self.slug})

    @models.permalink
    def get_questions_url(self):
        return ('questions', (), {'pslug': self.slug})

    @models.permalink
    def get_questions_create_url(self):
        return ('questions-create', (), {'pslug': self.slug})

    @models.permalink
    def get_documents_url(self):
        return ('documents', (), {'pslug': self.slug})

    @models.permalink
    def get_wiki_url(self):
        return ('wiki-page', (), {'pslug': self.slug, 'wslug': 'index'})


class ProjectUserRole(models.Model):
    project = models.ForeignKey("Project", related_name="user_roles")
    user = models.ForeignKey("auth.User", related_name="user_roles")
    role = models.ForeignKey("profile.Role", related_name="user_roles")

    mail_milestone_created = models.BooleanField(default=True)
    mail_milestone_modified = models.BooleanField(default=False)
    mail_milestone_deleted = models.BooleanField(default=False)
    mail_userstory_created = models.BooleanField(default=True)
    mail_userstory_modified = models.BooleanField(default=False)
    mail_userstory_deleted = models.BooleanField(default=False)
    mail_task_created = models.BooleanField(default=True)
    mail_task_assigned = models.BooleanField(default=False)
    mail_task_deleted = models.BooleanField(default=False)
    mail_question_created = models.BooleanField(default=False)
    mail_question_assigned = models.BooleanField(default=True)
    mail_question_deleted = models.BooleanField(default=False)
    mail_document_created = models.BooleanField(default=True)
    mail_document_deleted = models.BooleanField(default=False)
    mail_wiki_created = models.BooleanField(default=False)
    mail_wiki_modified = models.BooleanField(default=False)
    mail_wiki_deleted = models.BooleanField(default=False)

    def __repr__(self):
        return u"<Project-User-Relation-%s>" % (self.id)

    class Meta:
        unique_together = ('project', 'user')


class MilestoneManager(models.Manager):
    def get_by_natural_key(self, name, project):
        return self.get(name=name, project__slug=project)


class Milestone(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    name = models.CharField(max_length=200, db_index=True)
    owner = models.ForeignKey('auth.User', related_name="milestones")
    project = models.ForeignKey('Project', related_name="milestones")

    estimated_start = models.DateField(null=True, default=None)
    estimated_finish = models.DateField(null=True, default=None)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)

    disponibility = models.FloatField(null=True, default=0.0)
    objects = MilestoneManager()

    class Meta:
        ordering = ['-created_date']
        unique_together = ('name', 'project')

    @property
    def total_points(self):
        """
        Get total story points for this milestone.
        """

        total = sum(iter_points(self.user_stories.all()))
        return "{0:.1f}".format(total)

    def get_points_done_at_date(self, date):
        """
        Get completed story points for this milestone before the date.
        """
        total = 0.0

        for item in self.user_stories.filter(status__in=SCRUM_STATES.get_finished_us_states()):
            if item.tasks.filter(finished_date__lt=date).count() > 0:
                if item.points == -1:
                    continue

                if item.points == -2:
                    total += 0.5
                    continue

                total += item.points

        return "{0:.1f}".format(total)

    @property
    def completed_points(self):
        """
        Get a total of completed points.
        """

        queryset = self.user_stories.filter(status__in=SCRUM_STATES.get_finished_us_states())
        total = sum(iter_points(queryset))
        return "{0:.1f}".format(total)

    @property
    def percentage_completed(self):
        return "{0:.1f}".format(
            (float(self.completed_points) * 100) / float(self.total_points)
        )

    @models.permalink
    def get_absolute_url(self):
        return ('dashboard', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_edit_url(self):
        return ('milestone-edit', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_delete_url(self):
        return ('milestone-delete', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_dashboard_url(self):
        return ('dashboard', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_stats_url(self):
        return ('dashboard-api-stats', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_user_story_create_url(self):
        return ('user-story-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_ml_detail_url(self):
        return ('milestone-dashboard', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_create_task_url(self):
        # TODO: deprecated
        return ('api:task-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_stats_api_url(self):
        return ('api:stats-milestone', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_tasks_url(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id})

    @models.permalink
    def get_tasks_url_filter_by_task(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id, 'filter_by':'task'})

    @models.permalink
    def get_tasks_url_filter_by_bug(self):
        return ('tasks-view', (),
            {'pslug': self.project.slug, 'mid': self.id, 'filter_by':'bug'})

    @models.permalink
    def get_task_create_url(self):
        return ('task-create', (),
            {'pslug': self.project.slug, 'mid': self.id})

    class Meta(object):
        unique_together = ('name', 'project')

    def natural_key(self):
        return (self.name,) + self.project.natural_key()

    natural_key.dependencies = ['greenmine.Project']

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<Milestone %s>" % (self.id)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        super(Milestone, self).save(*args, **kwargs)


class UserStory(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    ref = models.CharField(max_length=200, db_index=True, null=True, default=None)
    milestone = models.ForeignKey("Milestone", blank=True,
        related_name="user_stories", null=True, default=None)
    project = models.ForeignKey("Project", related_name="user_stories")
    owner = models.ForeignKey("auth.User", null=True,
        default=None, related_name="user_stories")
    priority = models.IntegerField(default=1)
    points = models.IntegerField(choices=POINTS_CHOICES, default=-1)
    status = models.CharField(max_length=50,
        choices=SCRUM_STATES.get_us_choices(), db_index=True, default="open")

    tags = TaggableManager()

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    tested = models.BooleanField(default=False)

    subject = models.CharField(max_length=500)
    description = WikiField()
    finish_date = models.DateTimeField(null=True, blank=True)

    watchers = models.ManyToManyField('auth.User',
        related_name='us_watch', null=True)

    client_requirement = models.BooleanField(default=False)
    team_requirement = models.BooleanField(default=False)

    class Meta:
        unique_together = ('ref', 'project')

    def to_dict(self):
        return {
            "id": self.pk,
            "ref": self.ref,
            "subject": self.subject,
            "viewUrl": self.get_view_url(),
            "pointsDisplay": self.get_points_display(),
            "tags": [ {'id': tag.id, 'name': tag.name} for tag in self.tags.all() ]
        }

    def __repr__(self):
        return u"<UserStory %s>" % (self.id)

    def __unicode__(self):
        return u"{0} ({1})".format(self.subject, self.ref)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()
        if not self.ref:
            self.ref = ref_uniquely(self.project, self.__class__)

        super(UserStory, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('user-story', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_assign_url(self):
        return ('assign-us', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_unassign_url(self):
        return ('unassign-us', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_drop_api_url(self):
        # TODO: check if this url is used.
        return ('api:user-story-drop', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_view_url(self):
        return ('user-story', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_edit_url(self):
        return ('user-story-edit', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_edit_inline_url(self):
        return ('user-story-edit-inline', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_delete_url(self):
        return ('user-story-delete', (),
            {'pslug': self.project.slug, 'iref': self.ref})

    @models.permalink
    def get_task_create_url(self):
        return ('task-create', (),
            {'pslug': self.project.slug, 'usref': self.ref})

    """ Propertys """
    def update_status(self):
        tasks = self.tasks.all()
        used_states = []

        for task in tasks:
            used_states.append(task.fake_status)
        used_states = set(used_states)

        all_completed = True
        for state in SCRUM_STATES.ordered_us_states():
            for task_state in used_states:
                if task_state == state:
                    self.status = state
                    self.save()
                    return None
        return None

    @property
    def tasks_new(self):
        return self.tasks.filter(status__in=SCRUM_STATES.get_task_states_for_us_state('open'))

    @property
    def tasks_progress(self):
        return self.tasks.filter(status__in=SCRUM_STATES.get_task_states_for_us_state('progress'))

    @property
    def tasks_completed(self):
        return self.tasks.filter(status__in=SCRUM_STATES.get_task_states_for_us_state('completed'))

    @property
    def tasks_closed(self):
        return self.tasks.filter(status__in=SCRUM_STATES.get_task_states_for_us_state('closed'))


class Change(models.Model):
    change_type = models.IntegerField(choices=TASK_CHANGE_CHOICES)
    owner = models.ForeignKey('auth.User', related_name='changes')
    created_date = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey("Project", related_name="changes")

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    data = DictField()


class ChangeAttachment(models.Model):
    change = models.ForeignKey("Change", related_name="attachments")
    owner = models.ForeignKey("auth.User", related_name="change_attachments")

    created_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/msg",
        max_length=500, null=True, blank=True)


class TaskQuerySet(models.query.QuerySet):
    def _add_categories(self, section_dict, category_id, category_element, selected):
        section_dict[category_id] = section_dict.get(category_id, {
            'element': unicode(category_element),
            'count': 0,
            'id': category_id,
            'selected': selected,
        })
        section_dict[category_id]['count'] += 1

    def _get_category(self, section_dict, order_by='element', reverse=False):
        values = section_dict.values()
        values = sorted(values, key=lambda entry: unicode(entry[order_by]))
        if reverse:
            values.reverse()
        return values

    def _get_filter_and_build_filter_dict(self, queryset, milestone_id, status_id, tags_ids, assigned_to_id, severity_id):
        task_list = list(queryset)
        milestones = {}
        status = {}
        tags = {}
        assigned_to = {}
        severity = {}

        for task in task_list:
            if task.milestone:
                selected = milestone_id and task.milestone.id == milestone_id
                self._add_categories(milestones, task.milestone.id, task.milestone.name, selected)

            selected = status_id and task.status == status_id
            self._add_categories(status, task.status, task.get_status_display(), selected)

            for tag in task.tags.all():
                selected = tags_ids and tag.id in tags_ids
                self._add_categories(tags, tag.id, tag.name, selected)

            if task.assigned_to:
                selected = assigned_to_id and task.assigned_to.id == assigned_to_id
                self._add_categories(assigned_to, task.assigned_to.id, task.assigned_to.first_name, selected)

            selected = severity_id and task.severity == int(severity_id)
            self._add_categories(severity, task.severity, task.get_severity_display(), selected)

        return{
            'list': task_list,
            'filters' : {
                'milestones' : self._get_category(milestones),
                'status' : self._get_category(status),
                'tags' : self._get_category(tags),
                'assigned_to' : self._get_category(assigned_to),
                'severity' : self._get_category(severity),
            }
        }

    def filter_and_build_filter_dict(self, milestone=None, status=None, tags=None, assigned_to=None, severity=None):

        queryset = self
        if milestone:
            queryset = queryset.filter(milestone = milestone)

        if status:
            queryset = queryset.filter(status = status)

        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__in=[tag])

        if assigned_to:
            queryset = queryset.filter(assigned_to = assigned_to)

        if severity:
            queryset = queryset.filter(severity = severity)


        milestone_id = milestone and milestone.id
        status_id = status
        tags_ids = tags and tags.values_list('id', flat=True)
        assigned_to_id = assigned_to and assigned_to.id
        severity_id = severity

        return self._get_filter_and_build_filter_dict(queryset, milestone_id, status_id, tags_ids, assigned_to_id, severity_id)

class TaskManager(models.Manager):
    def get_query_set(self):
        return TaskQuerySet(self.model)


class Task(models.Model):
    uuid = models.CharField(max_length=40, unique=True, blank=True)
    user_story = models.ForeignKey('UserStory', related_name='tasks', null=True, blank=True)
    last_user_story = models.ForeignKey('UserStory', null=True, blank=True)
    ref = models.CharField(max_length=200, db_index=True, null=True, default=None)
    status = models.CharField(max_length=50,
        choices=TASK_STATUS_CHOICES, default='open')
    owner = models.ForeignKey("auth.User", null=True,
        default=None, related_name="tasks")

    severity = models.IntegerField(choices=TASK_SEVERITY_CHOICES, default=3)
    priority = models.IntegerField(choices=TASK_PRIORITY_CHOICES, default=3)
    milestone = models.ForeignKey('Milestone', related_name='tasks',
        null=True, default=None, blank=True)

    project = models.ForeignKey('Project', related_name='tasks')
    type = models.CharField(max_length=10,
        choices=TASK_TYPE_CHOICES, default='task')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    finished_date = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=50,
        choices=TASK_STATUS_CHOICES, null=True, blank=True)

    subject = models.CharField(max_length=500)
    description = WikiField(blank=True)
    assigned_to = models.ForeignKey('auth.User',
        related_name='user_storys_assigned_to_me',
        blank=True, null=True, default=None)

    watchers = models.ManyToManyField('auth.User',
        related_name='task_watch', null=True)

    changes = generic.GenericRelation(Change)

    tags = TaggableManager()

    objects = TaskManager()

    class Meta:
        unique_together = ('ref', 'project')

    def __unicode__(self):
        return self.subject

    @property
    def fake_status(self):
        return SCRUM_STATES.get_us_state_for_task_state(self.status)

    @models.permalink
    def get_absolute_url(self):
        if self.type == "bug":
            return ('issues-view', (), {'pslug':self.project.slug, 'tref': self.ref})
        else:
            return ('tasks-view', (), {'pslug':self.project.slug, 'tref': self.ref})

    @models.permalink
    def get_edit_url(self):
        if self.type == 'bug':
            return ('issues-edit', (),
                {'pslug': self.project.slug, 'tref': self.ref})
        else:
            #TODO: make this url
            return ('issues-edit', (),
                {'pslug': self.project.slug, 'tref': self.ref})
            #return ('tasks-edit', (),
                #{'pslug': self.project.slug, 'tref': self.ref})

    @models.permalink
    def get_view_url(self):
        if self.type == "bug":
            return ('issues-view', (), {'pslug':self.project.slug, 'tref': self.ref})
        else:
            return ('tasks-view', (), {'pslug':self.project.slug, 'tref': self.ref})

    @models.permalink
    def get_delete_url(self):
        if self.type == "bug":
            return ('issues-delete', (), {'pslug':self.project.slug, 'tref': self.ref})
        else:
            return ('tasks-delete', (), {'pslug':self.project.slug, 'tref': self.ref})

    def save(self, *args, **kwargs):
        last_user_story = None
        if self.last_user_story != self.user_story:
            last_user_story = self.last_user_story
            self.last_user_story = self.user_story

        if self.id:
            self.modified_date = timezone.now()
            # Store information about close date of a task
            if self.last_status != self.status:
                if self.last_status in SCRUM_STATES.get_finished_task_states():
                    if self.status in SCRUM_STATES.get_unfinished_task_states():
                        self.finished_date = None
                elif self.last_status in SCRUM_STATES.get_unfinished_task_states():
                    if self.status in SCRUM_STATES.get_finished_task_states():
                        self.finished_date = timezone.now()
                self.last_status = self.status

        if not self.ref:
            self.ref = ref_uniquely(self.project, self.__class__)

        super(Task, self).save(*args, **kwargs)

        if last_user_story:
            last_user_story.update_status()

        if self.user_story:
            self.user_story.update_status()


    def to_dict(self):
        self_dict = {
            'id': self.pk,
            'editUrl': self.get_edit_url(),
            'viewUrl': self.get_view_url(),
            'deleteUrl': self.get_delete_url(),
            'subject': self.subject,
            'type': self.get_type_display(),
            'statusDisplay': self.get_status_display(),
            'status': self.status,
            'fakeStatus': self.fake_status,
            'us': self.user_story and self.user_story.pk or None,
            'assignedTo': self.assigned_to and self.assigned_to.pk or None,
            'tags': [tag.to_dict() for tag in self.tags.all()],
            'priority': self.priority,
            'priorityDisplay': self.get_priority_display(),
            'severity': self.severity,
            'severityDisplay': self.get_severity_display(),
        }

        if self_dict['assignedTo']:
            self_dict['assignedToDisplay'] = self.assigned_to.get_full_name()
        else:
            self_dict['assignedToDisplay'] = ugettext("Unassigned")
        return self_dict


reversion.register(ProjectExtras)
reversion.register(Project)
reversion.register(ProjectUserRole)
reversion.register(Milestone)
reversion.register(UserStory)
reversion.register(Change)
reversion.register(ChangeAttachment)
reversion.register(Task)

from . import sigdispatch
