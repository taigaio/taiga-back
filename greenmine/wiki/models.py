from django.db import models

from greenmine.base.fields import DictField


class WikiPage(models.Model):
    project = models.ForeignKey('scrum.Project', related_name='wiki_pages')
    slug = models.SlugField(max_length=500, db_index=True)
    content = models.TextField(blank=False, null=True)
    owner = models.ForeignKey("base.User", related_name="wiki_pages", null=True)

    watchers = models.ManyToManyField('base.User',
                                      related_name='wikipage_watchers',
                                      null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ('can_view_wikipage', 'Can modify owned wiki pages'),
            ('can_change_owned_wikipage', 'Can modify owned wiki pages'),
        )


class WikiPageAttachment(models.Model):
    wikipage = models.ForeignKey('WikiPage', related_name='attachments')
    owner = models.ForeignKey("base.User", related_name="wikifiles")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/wiki", max_length=500,
                                     null=True, blank=True)
