from django.db import models

from greenmine.base.fields import DictField


class WikiPage(models.Model):
    project = models.ForeignKey('scrum.Project', related_name='wiki_pages')
    slug = models.SlugField(max_length=500, db_index=True)
    content = models.TextField(blank=False, null=True)
    owner = models.ForeignKey("base.User", related_name="wiki_pages", null=True, blank=True)

    watchers = models.ManyToManyField('base.User',
                                      related_name='wikipage_watchers',
                                      null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = u'wiki page'
        verbose_name_plural = u'wiki pages'
        ordering = ['project', 'slug']
        permissions = (
            ('can_view_wikipage', 'Can modify owned wiki pages'),
            ('can_change_owned_wikipage', 'Can modify owned wiki pages'),
        )

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.subject)


# TODO: why don't use scrum.Attachment?
class WikiPageAttachment(models.Model):
    wikipage = models.ForeignKey('WikiPage', related_name='attachments')
    owner = models.ForeignKey("base.User", related_name="wikifiles")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to="files/wiki", max_length=500,
                                     null=True, blank=True)

    class Meta:
        verbose_name = u'wiki page attachment'
        verbose_name_plural = u'wiki page attachments'
        ordering = ['wikipage', 'created_date']

    def __unicode__(self):
        return u"project {0} - page {1} - attachment {2}".format(self.wikipage.project_id, self.wikipage.subject, self.id)

