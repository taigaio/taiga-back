# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Membership'
        db.create_table('projects_membership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='memberships', to=orm['users.User'], null=True, blank=True, default=None)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='memberships', to=orm['projects.Project'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='memberships', to=orm['users.Role'])),
            ('email', self.gf('django.db.models.fields.EmailField')(null=True, max_length=255, default=None)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True, default=datetime.datetime.now)),
            ('token', self.gf('django.db.models.fields.CharField')(unique=True, blank=True, null=True, max_length=60, default=None)),
        ))
        db.send_create_signal('projects', ['Membership'])

        # Adding model 'Project'
        db.create_table('projects_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('default_points', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.Points'], null=True, on_delete=models.SET_NULL)),
            ('default_us_status', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.UserStoryStatus'], null=True, on_delete=models.SET_NULL)),
            ('default_task_status', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.TaskStatus'], null=True, on_delete=models.SET_NULL)),
            ('default_priority', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.Priority'], null=True, on_delete=models.SET_NULL)),
            ('default_severity', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.Severity'], null=True, on_delete=models.SET_NULL)),
            ('default_issue_status', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.IssueStatus'], null=True, on_delete=models.SET_NULL)),
            ('default_issue_type', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.IssueType'], null=True, on_delete=models.SET_NULL)),
            ('default_question_status', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, blank=True, to=orm['projects.QuestionStatus'], null=True, on_delete=models.SET_NULL)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=250)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, blank=True, max_length=250)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_projects', to=orm['users.User'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_us_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('last_task_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('last_issue_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, default=1)),
            ('total_milestones', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True, default=0)),
            ('total_story_points', self.gf('django.db.models.fields.FloatField')(null=True, default=None)),
            ('tags', self.gf('picklefield.fields.PickledObjectField')(blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(related_name='projects', null=True, to=orm['domains.Domain'], default=None)),
        ))
        db.send_create_signal('projects', ['Project'])

        # Adding model 'Attachment'
        db.create_table('projects_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='change_attachments', to=orm['users.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['projects.Project'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('attached_file', self.gf('django.db.models.fields.files.FileField')(null=True, blank=True, max_length=500)),
        ))
        db.send_create_signal('projects', ['Attachment'])

        # Adding model 'UserStoryStatus'
        db.create_table('projects_userstorystatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_statuses', to=orm['projects.Project'])),
        ))
        db.send_create_signal('projects', ['UserStoryStatus'])

        # Adding unique constraint on 'UserStoryStatus', fields ['project', 'name']
        db.create_unique('projects_userstorystatus', ['project_id', 'name'])

        # Adding model 'Points'
        db.create_table('projects_points', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True, default=None)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='points', to=orm['projects.Project'])),
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
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='task_statuses', to=orm['projects.Project'])),
        ))
        db.send_create_signal('projects', ['TaskStatus'])

        # Adding unique constraint on 'TaskStatus', fields ['project', 'name']
        db.create_unique('projects_taskstatus', ['project_id', 'name'])

        # Adding model 'Priority'
        db.create_table('projects_priority', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='priorities', to=orm['projects.Project'])),
        ))
        db.send_create_signal('projects', ['Priority'])

        # Adding unique constraint on 'Priority', fields ['project', 'name']
        db.create_unique('projects_priority', ['project_id', 'name'])

        # Adding model 'Severity'
        db.create_table('projects_severity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='severities', to=orm['projects.Project'])),
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
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='issue_statuses', to=orm['projects.Project'])),
        ))
        db.send_create_signal('projects', ['IssueStatus'])

        # Adding unique constraint on 'IssueStatus', fields ['project', 'name']
        db.create_unique('projects_issuestatus', ['project_id', 'name'])

        # Adding model 'IssueType'
        db.create_table('projects_issuetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='issue_types', to=orm['projects.Project'])),
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
            ('color', self.gf('django.db.models.fields.CharField')(max_length=20, default='#999999')),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='question_status', to=orm['projects.Project'])),
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

        # Deleting model 'Membership'
        db.delete_table('projects_membership')

        # Deleting model 'Project'
        db.delete_table('projects_project')

        # Deleting model 'Attachment'
        db.delete_table('projects_attachment')

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
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
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
        'domains.domain': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Domain'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '60', 'default': 'None'})
        },
        'projects.attachment': {
            'Meta': {'ordering': "['project', 'created_date']", 'object_name': 'Attachment'},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'change_attachments'", 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['projects.Project']"})
        },
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role']", 'object_name': 'Membership'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '255', 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'blank': 'True', 'null': 'True', 'max_length': '60', 'default': 'None'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'default': 'None'})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True', 'default': 'None'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Priority'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.IssueStatus']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.IssueType']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.Points']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.Priority']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.QuestionStatus']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.Severity']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.TaskStatus']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'blank': 'True', 'to': "orm['projects.UserStoryStatus']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects'", 'null': 'True', 'to': "orm['domains.Domain']", 'default': 'None'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': '0'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'})
        },
        'projects.questionstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'QuestionStatus'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Severity'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus'},
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
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#669933'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'max_length': '32', 'default': "'all_owned_projects'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200', 'default': 'None'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['projects']