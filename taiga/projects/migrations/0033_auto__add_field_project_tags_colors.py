# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.tags_colors'
        db.add_column('projects_project', 'tags_colors',
                      self.gf('djorm_pgarray.fields.TextArrayField')(blank=True, default={}, dimension=2, dbtype='text'),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.tags_colors'
        db.delete_column('projects_project', 'tags_colors')


    models = {
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueType', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'user__full_name', 'user__username', 'user__email', 'email']", 'object_name': 'Membership', 'unique_together': "(('user', 'project'),)"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True', 'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '255', 'null': 'True', 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '60', 'null': 'True', 'default': 'None'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'default': 'None', 'to': "orm['users.User']", 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Points', 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'null': 'True', 'default': 'None'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Priority', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'anon_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'null': 'True', 'default': '[]', 'dbtype': "'text'"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'default': 'None', 'to': "orm['projects.ProjectTemplate']", 'related_name': "'projects'"}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.IssueStatus']", 'unique': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.IssueType']", 'unique': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.Points']", 'unique': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.Priority']", 'unique': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.Severity']", 'unique': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.TaskStatus']", 'unique': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'on_delete': 'models.SET_NULL', 'blank': 'True', 'null': 'True', 'to': "orm['projects.UserStoryStatus']", 'unique': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'through': "orm['projects.Membership']", 'related_name': "'projects'", 'to': "orm['users.User']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'null': 'True', 'default': '[]', 'dbtype': "'text'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'null': 'True', 'default': 'None', 'dbtype': "'text'"}),
            'tags_colors': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'default': '{}', 'dimension': '2', 'dbtype': "'text'"}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True', 'default': '0'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'})
        },
        'projects.projecttemplate': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProjectTemplate'},
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
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '250', 'null': 'True'})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Severity', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'TaskStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'UserStoryStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"}),
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True', 'default': 'None'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role', 'unique_together': "(('slug', 'project'),)"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('djorm_pgarray.fields.TextArrayField', [], {'blank': 'True', 'null': 'True', 'default': '[]', 'dbtype': "'text'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True', 'default': "''"}),
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#31d025'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'email_token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True', 'default': 'None'}),
            'full_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '256'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'new_email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75', 'null': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '500', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True', 'default': 'None'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']
