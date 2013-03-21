from django.db import models


class WikiPage(models.Model):
    project = models.ForeignKey('scrum.Project', related_name='wiki_pages')
    slug = models.SlugField(max_length=500, db_index=True)
    content = models.TextField(blank=False, null=True)
    owner = models.ForeignKey("auth.User", related_name="wiki_pages", null=True)

    watchers = models.ManyToManyField('auth.User',
                                      related_name='wikipage_watchers',
                                      null=True)

    created_date = models.DateTimeField(auto_now_add=True)


class WikiPageHistory(models.Model):
    wikipage = models.ForeignKey("WikiPage", related_name="history_entries")
    content = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField()
    owner = models.ForeignKey("auth.User", related_name="wiki_page_historys")


class WikiPageAttachment(models.Model):
    wikipage = models.ForeignKey('WikiPage', related_name='attachments')
    owner = models.ForeignKey("auth.User", related_name="wikifiles")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/wiki", max_length=500,
                                     null=True, blank=True)
