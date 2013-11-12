# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'IssueStatus.color'
        db.add_column('projects_issuestatus', 'color',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999'),
                      keep_default=False)

        # Adding field 'Severity.color'
        db.add_column('projects_severity', 'color',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999'),
                      keep_default=False)

        # Adding field 'QuestionStatus.color'
        db.add_column('projects_questionstatus', 'color',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999'),
                      keep_default=False)

        # Adding field 'IssueType.color'
        db.add_column('projects_issuetype', 'color',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999'),
                      keep_default=False)


        # Changing field 'Project.default_issue_type'
        db.alter_column('projects_project', 'default_issue_type_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.IssueType']))

        # Changing field 'Project.default_points'
        db.alter_column('projects_project', 'default_points_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.Points']))

        # Changing field 'Project.default_priority'
        db.alter_column('projects_project', 'default_priority_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.Priority']))

        # Changing field 'Project.default_question_status'
        db.alter_column('projects_project', 'default_question_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.QuestionStatus']))

        # Changing field 'Project.default_us_status'
        db.alter_column('projects_project', 'default_us_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.UserStoryStatus']))

        # Changing field 'Project.default_severity'
        db.alter_column('projects_project', 'default_severity_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.Severity']))

        # Changing field 'Project.default_task_status'
        db.alter_column('projects_project', 'default_task_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.TaskStatus']))

        # Changing field 'Project.default_issue_status'
        db.alter_column('projects_project', 'default_issue_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['projects.IssueStatus']))
        # Adding field 'Priority.color'
        db.add_column('projects_priority', 'color',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999'),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'IssueStatus.color'
        db.delete_column('projects_issuestatus', 'color')

        # Deleting field 'Severity.color'
        db.delete_column('projects_severity', 'color')

        # Deleting field 'QuestionStatus.color'
        db.delete_column('projects_questionstatus', 'color')

        # Deleting field 'IssueType.color'
        db.delete_column('projects_issuetype', 'color')


        # Changing field 'Project.default_issue_type'
        db.alter_column('projects_project', 'default_issue_type_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.IssueType']))

        # Changing field 'Project.default_points'
        db.alter_column('projects_project', 'default_points_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.Points']))

        # Changing field 'Project.default_priority'
        db.alter_column('projects_project', 'default_priority_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.Priority']))

        # Changing field 'Project.default_question_status'
        db.alter_column('projects_project', 'default_question_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.QuestionStatus']))

        # Changing field 'Project.default_us_status'
        db.alter_column('projects_project', 'default_us_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.UserStoryStatus']))

        # Changing field 'Project.default_severity'
        db.alter_column('projects_project', 'default_severity_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.Severity']))

        # Changing field 'Project.default_task_status'
        db.alter_column('projects_project', 'default_task_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.TaskStatus']))

        # Changing field 'Project.default_issue_status'
        db.alter_column('projects_project', 'default_issue_status_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['projects.IssueStatus']))
        # Deleting field 'Priority.color'
        db.delete_column('projects_priority', 'color')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'db_table': "'django_content_type'", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'projects.attachment': {
            'Meta': {'ordering': "['project', 'created_date']", 'object_name': 'Attachment'},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'change_attachments'", 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['projects.Project']"})
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
            'Meta': {'ordering': "['project', 'role', 'user']", 'object_name': 'Membership', 'unique_together': "(('user', 'project'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.User']"})
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
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.IssueStatus']"}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.IssueType']"}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.Points']"}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.Priority']"}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.QuestionStatus']"}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.Severity']"}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.TaskStatus']"}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'related_name': "'+'", 'blank': 'True', 'to': "orm['projects.UserStoryStatus']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'through': "orm['projects.Membership']", 'symmetrical': 'False', 'related_name': "'projects'", 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': '0'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'})
        },
        'projects.questionstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'object_name': 'QuestionStatus', 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
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
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True', 'unique': 'True'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True', 'default': "'#669933'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True', 'default': "''"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'max_length': '32', 'default': "'all_owned_projects'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'default': 'None', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']