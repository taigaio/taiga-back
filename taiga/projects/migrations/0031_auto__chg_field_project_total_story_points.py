# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Project.total_story_points'
        db.alter_column('projects_project', 'total_story_points', self.gf('django.db.models.fields.FloatField')())

    def backwards(self, orm):

        # Changing field 'Project.total_story_points'
        db.alter_column('projects_project', 'total_story_points', self.gf('django.db.models.fields.FloatField')(null=True))

    models = {
        'projects.issuestatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'unique_together': "(('user', 'project'),)", 'object_name': 'Membership', 'ordering': "['project', 'user__full_name', 'user__username', 'user__email', 'email']"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True', 'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'max_length': '60'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'blank': 'True', 'default': 'None', 'null': 'True', 'to': "orm['users.User']"})
        },
        'projects.points': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Points', 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': 'None', 'null': 'True'})
        },
        'projects.priority': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Priority', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'anon_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects'", 'blank': 'True', 'default': 'None', 'null': 'True', 'to': "orm['projects.ProjectTemplate']"}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.IssueStatus']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.IssueType']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.Points']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.Priority']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.Severity']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.TaskStatus']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'to': "orm['projects.UserStoryStatus']", 'on_delete': 'models.SET_NULL', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'to': "orm['users.User']", 'through': "orm['projects.Membership']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'public_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'dbtype': "'text'"}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'})
        },
        'projects.projecttemplate': {
            'Meta': {'object_name': 'ProjectTemplate', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
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
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'points': ('django_pgjson.fields.JsonField', [], {}),
            'priorities': ('django_pgjson.fields.JsonField', [], {}),
            'roles': ('django_pgjson.fields.JsonField', [], {}),
            'severities': ('django_pgjson.fields.JsonField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'})
        },
        'projects.severity': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Severity', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"}),
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': 'None', 'null': 'True'})
        },
        'users.role': {
            'Meta': {'unique_together': "(('slug', 'project'),)", 'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '[]', 'null': 'True', 'dbtype': "'text'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True', 'default': "''"}),
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'#264f49'", 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'full_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '256'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'null': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']