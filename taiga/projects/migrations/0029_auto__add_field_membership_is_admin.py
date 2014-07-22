# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Membership.is_admin'
        db.add_column('projects_membership', 'is_admin',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Membership.is_admin'
        db.delete_column('projects_membership', 'is_admin')


    models = {
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'Meta': {'ordering': "['project', 'role']", 'object_name': 'Membership', 'unique_together': "(('user', 'project'),)"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True', 'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'blank': 'True', 'max_length': '255', 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '60', 'default': 'None'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'memberships'", 'default': 'None'})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Points', 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True', 'default': 'None'})
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
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['projects.ProjectTemplate']", 'related_name': "'projects'", 'default': 'None'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueStatus']"}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.IssueType']"}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Points']"}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Priority']"}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.Severity']"}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.TaskStatus']"}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'to': "orm['projects.UserStoryStatus']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'tags': ('djorm_pgarray.fields.TextArrayField', [], {'null': 'True', 'blank': 'True', 'dbtype': "'text'", 'default': 'None'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': '0'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'})
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
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'})
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
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': 'None'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role', 'unique_together': "(('slug', 'project'),)"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles'", 'to': "orm['auth.Permission']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True', 'default': "''"}),
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#2ab1df'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'full_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '256'}),
            'github_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200', 'default': 'None'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']