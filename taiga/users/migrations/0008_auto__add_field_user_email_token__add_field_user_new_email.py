# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.email_token'
        db.add_column('users_user', 'email_token',
                      self.gf('django.db.models.fields.CharField')(default=None, blank=True, null=True, max_length=200),
                      keep_default=False)

        # Adding field 'User.new_email'
        db.add_column('users_user', 'new_email',
                      self.gf('django.db.models.fields.EmailField')(blank=True, null=True, max_length=75),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.email_token'
        db.delete_column('users_user', 'email_token')

        # Deleting field 'User.new_email'
        db.delete_column('users_user', 'new_email')


    models = {
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_statuses'"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueType', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_types'"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'user__full_name', 'user__username', 'user__email', 'email']", 'object_name': 'Membership', 'unique_together': "(('user', 'project'),)"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'auto_now_add': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'blank': 'True', 'null': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'blank': 'True', 'null': 'True', 'max_length': '60'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'default': 'None', 'blank': 'True', 'null': 'True', 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Points', 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'default': 'None', 'blank': 'True', 'null': 'True'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Priority', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'priorities'"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'anon_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'default': '[]', 'blank': 'True', 'null': 'True', 'dbtype': "'text'"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.ProjectTemplate']", 'default': 'None', 'blank': 'True', 'null': 'True', 'related_name': "'projects'"}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueStatus']", 'unique': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueType']", 'unique': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Points']", 'unique': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Priority']", 'unique': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Severity']", 'unique': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.TaskStatus']", 'unique': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.UserStoryStatus']", 'unique': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['users.User']", 'symmetrical': 'False', 'through': "orm['projects.Membership']", 'related_name': "'projects'"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'public_permissions': ('djorm_pgarray.fields.TextArrayField', [], {'default': '[]', 'blank': 'True', 'null': 'True', 'dbtype': "'text'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'default': 'None', 'blank': 'True', 'null': 'True', 'dbtype': "'text'"}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'})
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
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '250'})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Severity', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'severities'"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'TaskStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'task_statuses'"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'UserStoryStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'us_statuses'"}),
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'blank': 'True', 'null': 'True'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role', 'unique_together': "(('slug', 'project'),)"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('djorm_pgarray.fields.TextArrayField', [], {'default': '[]', 'blank': 'True', 'null': 'True', 'dbtype': "'text'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True', 'default': "''"}),
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'#d8b489'", 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'email_token': ('django.db.models.fields.CharField', [], {'default': 'None', 'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'full_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '256'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'new_email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'null': 'True', 'max_length': '75'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'null': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['users']