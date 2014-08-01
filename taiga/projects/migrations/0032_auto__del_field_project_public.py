# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Project.public'
        db.delete_column('projects_project', 'public')


    def backwards(self, orm):
        # Adding field 'Project.public'
        db.add_column('projects_project', 'public',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    models = {
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True', 'auto_now_add': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'default': 'None', 'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '60', 'default': 'None', 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'default': 'None', 'blank': 'True', 'null': 'True', 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Points', 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'default': 'None', 'blank': 'True', 'null': 'True'})
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
            'anon_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'dbtype': "'text'", 'default': '[]', 'blank': 'True', 'null': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.ProjectTemplate']", 'default': 'None', 'blank': 'True', 'null': 'True', 'related_name': "'projects'"}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.IssueStatus']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.IssueType']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.Points']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.Priority']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.Severity']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.TaskStatus']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'on_delete': 'models.SET_NULL', 'unique': 'True', 'to': "orm['projects.UserStoryStatus']", 'related_name': "'+'", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'dbtype': "'text'", 'default': '[]', 'blank': 'True', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'dbtype': "'text'", 'default': 'None', 'blank': 'True', 'null': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True', 'null': 'True'})
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
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True', 'null': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True', 'null': 'True'})
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
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'blank': 'True', 'null': 'True'})
        },
        'users.role': {
            'Meta': {'unique_together': "(('slug', 'project'),)", 'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('djorm_pgarray.fields.TextArrayField', [], {'dbtype': "'text'", 'default': '[]', 'blank': 'True', 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'bio': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '9', 'default': "'#410878'", 'blank': 'True'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'max_length': '500', 'blank': 'True', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'default': 'None', 'blank': 'True', 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']