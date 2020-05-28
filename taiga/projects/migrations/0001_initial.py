# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields
import django.utils.timezone
import django.db.models.deletion
import taiga.projects.history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0002_auto_20140903_0916'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('is_owner', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=255, null=True, default=None, verbose_name='email', blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creado el')),
                ('token', models.CharField(max_length=60, null=True, default=None, verbose_name='token', blank=True)),
                ('invited_by_id', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ['project', 'user__full_name', 'user__username', 'user__email', 'email'],
                'verbose_name_plural': 'membershipss',
                'verbose_name': 'membership',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=list, null=True, size=None, verbose_name='tags')),
                ('name', models.CharField(max_length=250, unique=True, verbose_name='name')),
                ('slug', models.SlugField(max_length=250, unique=True, verbose_name='slug', blank=True)),
                ('description', models.TextField(verbose_name='description')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('total_milestones', models.IntegerField(null=True, default=0, verbose_name='total of milestones', blank=True)),
                ('total_story_points', models.FloatField(default=0, verbose_name='total story points')),
                ('is_backlog_activated', models.BooleanField(default=True, verbose_name='active backlog panel')),
                ('is_kanban_activated', models.BooleanField(default=False, verbose_name='active kanban panel')),
                ('is_wiki_activated', models.BooleanField(default=True, verbose_name='active wiki panel')),
                ('is_issues_activated', models.BooleanField(default=True, verbose_name='active issues panel')),
                ('videoconferences', models.CharField(max_length=250, null=True, choices=[('appear-in', 'AppearIn'), ('talky', 'Talky')], verbose_name='videoconference system', blank=True)),
                ('videoconferences_salt', models.CharField(max_length=250, null=True, verbose_name='videoconference room salt', blank=True)),
                ('anon_permissions', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(choices=[('view_project', 'View project'), ('view_milestones', 'View milestones'), ('view_us', 'View user stories'), ('view_tasks', 'View tasks'), ('view_issues', 'View issues'), ('view_wiki_pages', 'View wiki pages'), ('view_wiki_links', 'View wiki links')]), blank=True, default=list, null=True, size=None, verbose_name='anonymous permissions')),
                ('public_permissions', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(choices=[('view_project', 'View project'), ('view_milestones', 'View milestones'), ('view_us', 'View user stories'), ('view_issues', 'View issues'), ('vote_issues', 'Vote issues'), ('view_tasks', 'View tasks'), ('view_wiki_pages', 'View wiki pages'), ('view_wiki_links', 'View wiki links'), ('request_membership', 'Request membership'), ('add_us_to_project', 'Add user story to project'), ('add_comments_to_us', 'Add comments to user stories'), ('add_comments_to_task', 'Add comments to tasks'), ('add_issue', 'Add issues'), ('add_comments_issue', 'Add comments to issues'), ('add_wiki_page', 'Add wiki page'), ('modify_wiki_page', 'Modify wiki page'), ('add_wiki_link', 'Add wiki link'), ('modify_wiki_link', 'Modify wiki link')]), blank=True, default=list, null=True, size=None, verbose_name='user permissions')),
                ('is_private', models.BooleanField(default=False, verbose_name='is private')),
                ('tags_colors', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True, null=True), size=2), blank=True, default=list, null=True, size=None, verbose_name='tags colors')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'projects',
                'verbose_name': 'project',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='project',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='projects', verbose_name='members', through='projects.Membership'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='owner',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='owned_projects', verbose_name='owner', on_delete=models.SET_NULL),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(blank=True, default=None, to=settings.AUTH_USER_MODEL, null=True, related_name='memberships', on_delete=models.CASCADE),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='membership',
            name='project',
            field=models.ForeignKey(default=1, to='projects.Project', related_name='memberships', on_delete=models.CASCADE),
            preserve_default=False,
        ),

        migrations.AlterUniqueTogether(
            name='membership',
            unique_together=set([('user', 'project')]),
        ),

        migrations.AddField(
            model_name='membership',
            name='role',
            field=models.ForeignKey(related_name='memberships', to='users.Role', default=1, on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
