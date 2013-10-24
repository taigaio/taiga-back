# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Attachment'
        db.create_table('projects_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], related_name='change_attachments')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='attachments')),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('attached_file', self.gf('django.db.models.fields.files.FileField')(null=True, blank=True, max_length=500)),
        ))
        db.send_create_signal('projects', ['Attachment'])

        # Adding model 'Membership'
        db.create_table('projects_membership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], related_name='memberships')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='memberships')),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Role'], related_name='memberships')),
        ))
        db.send_create_signal('projects', ['Membership'])

        # Adding unique constraint on 'Membership', fields ['user', 'project']
        db.create_unique('projects_membership', ['user_id', 'project_id'])

        # Adding model 'Project'
        db.create_table('projects_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=40, unique=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, unique=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=250, unique=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], related_name='owned_projects')),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_us_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('last_task_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('last_issue_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('total_milestones', self.gf('django.db.models.fields.IntegerField')(null=True, default=0, blank=True)),
            ('total_story_points', self.gf('django.db.models.fields.FloatField')(null=True, default=None)),
            ('tags', self.gf('picklefield.fields.PickledObjectField')(blank=True)),
        ))
        db.send_create_signal('projects', ['Project'])

        # Adding model 'UserStoryStatus'
        db.create_table('projects_userstorystatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='us_statuses')),
        ))
        db.send_create_signal('projects', ['UserStoryStatus'])

        # Adding unique constraint on 'UserStoryStatus', fields ['project', 'name']
        db.create_unique('projects_userstorystatus', ['project_id', 'name'])

        # Adding model 'Points'
        db.create_table('projects_points', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('value', self.gf('django.db.models.fields.FloatField')(null=True, default=None, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='points')),
        ))
        db.send_create_signal('projects', ['Points'])

        # Adding unique constraint on 'Points', fields ['project', 'name']
        db.create_unique('projects_points', ['project_id', 'name'])

        # Adding model 'TaskStatus'
        db.create_table('projects_taskstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='task_statuses')),
        ))
        db.send_create_signal('projects', ['TaskStatus'])

        # Adding unique constraint on 'TaskStatus', fields ['project', 'name']
        db.create_unique('projects_taskstatus', ['project_id', 'name'])

        # Adding model 'Priority'
        db.create_table('projects_priority', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='priorities')),
        ))
        db.send_create_signal('projects', ['Priority'])

        # Adding unique constraint on 'Priority', fields ['project', 'name']
        db.create_unique('projects_priority', ['project_id', 'name'])

        # Adding model 'Severity'
        db.create_table('projects_severity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='severities')),
        ))
        db.send_create_signal('projects', ['Severity'])

        # Adding unique constraint on 'Severity', fields ['project', 'name']
        db.create_unique('projects_severity', ['project_id', 'name'])

        # Adding model 'IssueStatus'
        db.create_table('projects_issuestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='issue_statuses')),
        ))
        db.send_create_signal('projects', ['IssueStatus'])

        # Adding unique constraint on 'IssueStatus', fields ['project', 'name']
        db.create_unique('projects_issuestatus', ['project_id', 'name'])

        # Adding model 'IssueType'
        db.create_table('projects_issuetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='issue_types')),
        ))
        db.send_create_signal('projects', ['IssueType'])

        # Adding unique constraint on 'IssueType', fields ['project', 'name']
        db.create_unique('projects_issuetype', ['project_id', 'name'])

        # Adding model 'QuestionStatus'
        db.create_table('projects_questionstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='question_status')),
        ))
        db.send_create_signal('projects', ['QuestionStatus'])

        # Adding unique constraint on 'QuestionStatus', fields ['project', 'name']
        db.create_unique('projects_questionstatus', ['project_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'QuestionStatus', fields ['project', 'name']
        db.delete_unique('projects_questionstatus', ['project_id', 'name'])

        # Removing unique constraint on 'IssueType', fields ['project', 'name']
        db.delete_unique('projects_issuetype', ['project_id', 'name'])

        # Removing unique constraint on 'IssueStatus', fields ['project', 'name']
        db.delete_unique('projects_issuestatus', ['project_id', 'name'])

        # Removing unique constraint on 'Severity', fields ['project', 'name']
        db.delete_unique('projects_severity', ['project_id', 'name'])

        # Removing unique constraint on 'Priority', fields ['project', 'name']
        db.delete_unique('projects_priority', ['project_id', 'name'])

        # Removing unique constraint on 'TaskStatus', fields ['project', 'name']
        db.delete_unique('projects_taskstatus', ['project_id', 'name'])

        # Removing unique constraint on 'Points', fields ['project', 'name']
        db.delete_unique('projects_points', ['project_id', 'name'])

        # Removing unique constraint on 'UserStoryStatus', fields ['project', 'name']
        db.delete_unique('projects_userstorystatus', ['project_id', 'name'])

        # Removing unique constraint on 'Membership', fields ['user', 'project']
        db.delete_unique('projects_membership', ['user_id', 'project_id'])

        # Deleting model 'Attachment'
        db.delete_table('projects_attachment')

        # Deleting model 'Membership'
        db.delete_table('projects_membership')

        # Deleting model 'Project'
        db.delete_table('projects_project')

        # Deleting model 'UserStoryStatus'
        db.delete_table('projects_userstorystatus')

        # Deleting model 'Points'
        db.delete_table('projects_points')

        # Deleting model 'TaskStatus'
        db.delete_table('projects_taskstatus')

        # Deleting model 'Priority'
        db.delete_table('projects_priority')

        # Deleting model 'Severity'
        db.delete_table('projects_severity')

        # Deleting model 'IssueStatus'
        db.delete_table('projects_issuestatus')

        # Deleting model 'IssueType'
        db.delete_table('projects_issuetype')

        # Deleting model 'QuestionStatus'
        db.delete_table('projects_questionstatus')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'projects.attachment': {
            'Meta': {'ordering': "['project', 'created_date']", 'object_name': 'Attachment'},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'change_attachments'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'attachments'"})
        },
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_statuses'"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_types'"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role', 'user']", 'unique_together': "(('user', 'project'),)", 'object_name': 'Membership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Priority'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'priorities'"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'through': "orm['projects.Membership']", 'to': "orm['users.User']", 'symmetrical': 'False', 'related_name': "'projects'"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': '0', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'blank': 'True'})
        },
        'projects.questionstatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'QuestionStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'question_status'"})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Severity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'severities'"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'task_statuses'"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'us_statuses'"})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role'},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '9', 'default': "'#669933'", 'blank': 'True'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'default': 'None', 'max_length': '200'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['projects']