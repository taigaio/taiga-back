# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        for project in orm["projects.Project"].objects.all():
            project.domain = project.site
            project.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'domains.domain': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Domain'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '60', 'default': 'None', 'null': 'True'})
        },
        'projects.attachment': {
            'Meta': {'ordering': "['project', 'created_date']", 'object_name': 'Attachment'},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '500', 'null': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'change_attachments'", 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['projects.Project']"})
        },
        'projects.issuestatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'IssueStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'IssueType'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role']", 'object_name': 'Membership'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'auto_now_add': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True', 'unique': 'True', 'default': 'None', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'blank': 'True', 'to': "orm['users.User']", 'default': 'None', 'null': 'True'})
        },
        'projects.points': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': 'None', 'null': 'True'})
        },
        'projects.priority': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'Priority'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.IssueStatus']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.IssueType']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.Points']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.Priority']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.QuestionStatus']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.Severity']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.TaskStatus']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['projects.UserStoryStatus']", 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects'", 'to': "orm['domains.Domain']", 'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'to': "orm['users.User']", 'through': "orm['projects.Membership']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['domains.Domain']", 'default': 'None', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'})
        },
        'projects.questionstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'QuestionStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
        },
        'projects.severity': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'Severity'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'TaskStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']", 'object_name': 'UserStoryStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role'},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles'", 'to': "orm['auth.Permission']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'#669933'", 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'default': "'all_owned_projects'", 'max_length': '32'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '500', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'default': 'None', 'null': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']
    symmetrical = True
