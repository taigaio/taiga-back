# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RolePoints'
        db.create_table('userstories_rolepoints', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_story', self.gf('django.db.models.fields.related.ForeignKey')(related_name='role_points', to=orm['userstories.UserStory'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='role_points', to=orm['users.Role'])),
            ('points', self.gf('django.db.models.fields.related.ForeignKey')(related_name='role_points', to=orm['projects.Points'])),
        ))
        db.send_create_signal('userstories', ['RolePoints'])

        # Adding unique constraint on 'RolePoints', fields ['user_story', 'role']
        db.create_unique('userstories_rolepoints', ['user_story_id', 'role_id'])

        # Adding model 'UserStory'
        db.create_table('userstories_userstory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=40, unique=True, blank=True)),
            ('ref', self.gf('django.db.models.fields.BigIntegerField')(db_index=True, null=True, default=None, blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(null=True, blank=True, to=orm['milestones.Milestone'], default=None, related_name='user_stories', on_delete=models.SET_NULL)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_stories', to=orm['projects.Project'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(null=True, blank=True, related_name='owned_user_stories', to=orm['users.User'], on_delete=models.SET_NULL)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(null=True, blank=True, related_name='user_stories', to=orm['projects.UserStoryStatus'], on_delete=models.SET_NULL)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=100)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now=True)),
            ('finish_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('client_requirement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('team_requirement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tags', self.gf('picklefield.fields.PickledObjectField')(blank=True)),
        ))
        db.send_create_signal('userstories', ['UserStory'])

        # Adding unique constraint on 'UserStory', fields ['ref', 'project']
        db.create_unique('userstories_userstory', ['ref', 'project_id'])

        # Adding M2M table for field watchers on 'UserStory'
        m2m_table_name = db.shorten_name('userstories_userstory_watchers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userstory', models.ForeignKey(orm['userstories.userstory'], null=False)),
            ('user', models.ForeignKey(orm['users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userstory_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserStory', fields ['ref', 'project']
        db.delete_unique('userstories_userstory', ['ref', 'project_id'])

        # Removing unique constraint on 'RolePoints', fields ['user_story', 'role']
        db.delete_unique('userstories_rolepoints', ['user_story_id', 'role_id'])

        # Deleting model 'RolePoints'
        db.delete_table('userstories_rolepoints')

        # Deleting model 'UserStory'
        db.delete_table('userstories_userstory')

        # Removing M2M table for field watchers on 'UserStory'
        db.delete_table(db.shorten_name('userstories_userstory_watchers'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
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
        'milestones.milestone': {
            'Meta': {'ordering': "['project', '-created_date']", 'unique_together': "(('name', 'project'),)", 'object_name': 'Milestone'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': '0.0', 'blank': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'null': 'True', 'default': 'None', 'blank': 'True'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'default': 'None', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'related_name': "'owned_milestones'", 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'blank': 'True'})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role', 'user']", 'unique_together': "(('user', 'project'),)", 'object_name': 'Membership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.User']"})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'through': "orm['projects.Membership']", 'symmetrical': 'False', 'related_name': "'projects'", 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': '0', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'blank': 'True'})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'default': 'None', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'userstories.rolepoints': {
            'Meta': {'unique_together': "(('user_story', 'role'),)", 'object_name': 'RolePoints'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['projects.Points']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['users.Role']"}),
            'user_story': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['userstories.UserStory']"})
        },
        'userstories.userstory': {
            'Meta': {'ordering': "['project', 'order']", 'unique_together': "(('ref', 'project'),)", 'object_name': 'UserStory'},
            'client_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['milestones.Milestone']", 'default': 'None', 'related_name': "'user_stories'", 'on_delete': 'models.SET_NULL'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'related_name': "'owned_user_stories'", 'to': "orm['users.User']", 'on_delete': 'models.SET_NULL'}),
            'points': ('django.db.models.fields.related.ManyToManyField', [], {'through': "orm['userstories.RolePoints']", 'symmetrical': 'False', 'related_name': "'userstories'", 'to': "orm['projects.Points']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'to': "orm['projects.Project']"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True', 'null': 'True', 'default': 'None', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'related_name': "'user_stories'", 'to': "orm['projects.UserStoryStatus']", 'on_delete': 'models.SET_NULL'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'team_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'blank': 'True'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'null': 'True', 'blank': 'True', 'symmetrical': 'False', 'related_name': "'watched_us'", 'to': "orm['users.User']"})
        }
    }

    complete_apps = ['userstories']