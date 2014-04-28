# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ProjectTemplate.default_owner_role'
        db.add_column('projects_projecttemplate', 'default_owner_role',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ProjectTemplate.default_owner_role'
        db.delete_column('projects_projecttemplate', 'default_owner_role')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
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
        'domains.domain': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Domain'},
            'alias_of': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'+'", 'blank': 'True', 'to': "orm['domains.Domain']", 'default': 'None'}),
            'default_language': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '20'}),
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'null': 'True', 'default': 'None', 'max_length': '60'})
        },
        'projects.attachment': {
            'Meta': {'ordering': "['project', 'created_date']", 'object_name': 'Attachment'},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'change_attachments'", 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['projects.Project']"})
        },
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'IssueType', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role']", 'object_name': 'Membership'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True', 'auto_now_add': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'default': 'None', 'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'default': 'None', 'blank': 'True', 'max_length': '60'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'memberships'", 'blank': 'True', 'to': "orm['users.User']", 'default': 'None'})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Points', 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Priority', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'creation_template': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['projects.ProjectTemplate']", 'default': 'None'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.IssueStatus']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.IssueType']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Points']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Priority']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.QuestionStatus']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Severity']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.TaskStatus']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.UserStoryStatus']", 'unique': 'True', 'related_name': "'+'", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['domains.Domain']", 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '0'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '0'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '0'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'through': "orm['projects.Membership']", 'symmetrical': 'False', 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': '0', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'projects.projecttemplate': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProjectTemplate'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'default_options': ('django_pgjson.fields.JsonField', [], {}),
            'default_owner_role': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'templates'", 'blank': 'True', 'to': "orm['domains.Domain']", 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'issue_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'issue_types': ('django_pgjson.fields.JsonField', [], {}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'points': ('django_pgjson.fields.JsonField', [], {}),
            'priorities': ('django_pgjson.fields.JsonField', [], {}),
            'roles': ('django_pgjson.fields.JsonField', [], {}),
            'severities': ('django_pgjson.fields.JsonField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'task_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'us_statuses': ('django_pgjson.fields.JsonField', [], {}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'projects.questionstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'QuestionStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'Severity', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'TaskStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'UserStoryStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"}),
            'wip_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role', 'unique_together': "(('slug', 'project'),)"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#d4ca2f'", 'blank': 'True', 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'default': "'all_owned_projects'", 'max_length': '32'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'default': 'None', 'blank': 'True', 'max_length': '200'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['projects']