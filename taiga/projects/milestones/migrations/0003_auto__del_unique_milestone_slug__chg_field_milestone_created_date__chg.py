# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Milestone', fields ['slug']
        db.delete_unique('milestones_milestone', ['slug'])


        # Changing field 'Milestone.created_date'
        db.alter_column('milestones_milestone', 'created_date', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Milestone.modified_date'
        db.alter_column('milestones_milestone', 'modified_date', self.gf('django.db.models.fields.DateTimeField')())
        # Adding unique constraint on 'Milestone', fields ['slug', 'project']
        db.create_unique('milestones_milestone', ['slug', 'project_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Milestone', fields ['slug', 'project']
        db.delete_unique('milestones_milestone', ['slug', 'project_id'])

        # Adding unique constraint on 'Milestone', fields ['slug']
        db.create_unique('milestones_milestone', ['slug'])


        # Changing field 'Milestone.created_date'
        db.alter_column('milestones_milestone', 'created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Milestone.modified_date'
        db.alter_column('milestones_milestone', 'modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

    models = {
        'milestones.milestone': {
            'Meta': {'unique_together': "[('name', 'project'), ('slug', 'project')]", 'object_name': 'Milestone', 'ordering': "['project', 'created_date']"},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': '0.0', 'null': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {}),
            'estimated_start': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'owned_milestones'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'milestones'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['users.User']", 'symmetrical': 'False', 'null': 'True', 'related_name': "'milestones_milestone+'"})
        },
        'projects.issuestatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_statuses'"})
        },
        'projects.issuetype': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_types'"})
        },
        'projects.membership': {
            'Meta': {'unique_together': "(('user', 'project'),)", 'object_name': 'Membership', 'ordering': "['project', 'user__full_name', 'user__username', 'user__email', 'email']"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '255', 'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '60', 'default': 'None', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'default': 'None', 'null': 'True', 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Points', 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': 'None', 'null': 'True'})
        },
        'projects.priority': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Priority', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'priorities'"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'anon_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['projects.ProjectTemplate']", 'default': 'None', 'null': 'True', 'related_name': "'projects'"}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueStatus']", 'unique': 'True', 'null': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueType']", 'unique': 'True', 'null': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Points']", 'unique': 'True', 'null': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Priority']", 'unique': 'True', 'null': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Severity']", 'unique': 'True', 'null': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.TaskStatus']", 'unique': 'True', 'null': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.UserStoryStatus']", 'unique': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['users.User']", 'through': "orm['projects.Membership']", 'symmetrical': 'False', 'related_name': "'projects'"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'dbtype': "'text'"}),
            'tags_colors': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'dbtype': "'text'", 'dimension': '2'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'})
        },
        'projects.projecttemplate': {
            'Meta': {'object_name': 'ProjectTemplate', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_options': ('django_pgjson.fields.JsonField', [], {}),
            'default_owner_role': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'issue_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'issue_types': ('django_pgjson.fields.JsonField', [], {}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'points': ('django_pgjson.fields.JsonField', [], {}),
            'priorities': ('django_pgjson.fields.JsonField', [], {}),
            'roles': ('django_pgjson.fields.JsonField', [], {}),
            'severities': ('django_pgjson.fields.JsonField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'})
        },
        'projects.severity': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Severity', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'severities'"})
        },
        'projects.taskstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'task_statuses'"})
        },
        'projects.userstorystatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'us_statuses'"}),
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': 'None', 'null': 'True'})
        },
        'users.role': {
            'Meta': {'unique_together': "(('slug', 'project'),)", 'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True', 'default': "''"}),
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#3f564d'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'email_token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'default': 'None', 'null': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '256'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'new_email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75', 'null': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '500', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'default': 'None', 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['milestones']