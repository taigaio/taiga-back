# -*- coding: utf-8 -*-
from __future__ import absolute_import

import django
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import connection, models, IntegrityError, transaction
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify as default_slugify
from django.utils.translation import ugettext_lazy as _, ugettext
qn = connection.ops.quote_name

class TagBase(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    slug = models.SlugField(verbose_name=_('Slug'), unique=True, max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = self.slugify(self.name)
            if django.VERSION >= (1, 2):
                from django.db import router
                using = kwargs.get("using") or router.db_for_write(
                    type(self), instance=self)
                # Make sure we write to the same db for all attempted writes,
                # with a multi-master setup, theoretically we could try to
                # write and rollback on different DBs
                kwargs["using"] = using
                trans_kwargs = {"using": using}
            else:
                trans_kwargs = {}
            i = 0
            while True:
                i += 1
                try:
                    sid = transaction.savepoint(**trans_kwargs)
                    res = super(TagBase, self).save(*args, **kwargs)
                    transaction.savepoint_commit(sid, **trans_kwargs)
                    return res
                except IntegrityError:
                    transaction.savepoint_rollback(sid, **trans_kwargs)
                    self.slug = self.slugify(self.name, i)
        else:
            return super(TagBase, self).save(*args, **kwargs)

    def slugify(self, tag, i=None):
        slug = default_slugify(tag)
        if i is not None:
            slug += "_%d" % i
        return slug


class TagManager(models.Manager):
    def tags_for_queryset(self, queryset, counts=True, min_count=None):
        """
        Obtain a list of tags associated with instances of a model
        contained in the given queryset.

        If ``counts`` is True, a ``count`` attribute will be added to
        each tag, indicating how many times it has been used against
        the Model class in question.

        If ``min_count`` is given, only tags which have a ``count``
        greater than or equal to ``min_count`` will be returned.
        Passing a value for ``min_count`` implies ``counts=True``.
        """

        compiler = queryset.query.get_compiler(using='default')
        extra_joins = ' '.join(compiler.get_from_clause()[0][1:])
        where, params = queryset.query.where.as_sql(
            compiler.quote_name_unless_alias, compiler.connection
        )

        if where:
            extra_criteria = 'AND %s' % where
        else:
            extra_criteria = ''
        return self._get_usage(queryset.model, counts, min_count, extra_joins, extra_criteria, params)



    def _get_usage(self, model, counts=False, min_count=None, extra_joins=None, extra_criteria=None, params=None):
        """
        Perform the custom SQL query for ``usage_for_model`` and
        ``usage_for_queryset``.
        """
        if min_count is not None: counts = True

        model_table = qn(model._meta.db_table)
        model_pk = '%s.%s' % (model_table, qn(model._meta.pk.column))

        query = """
        SELECT DISTINCT %(tag)s.id, %(tag)s.name%(count_sql)s
        FROM
            %(tag)s
            INNER JOIN %(tagged_item_alias)s
                ON %(tag)s.id = %(tagged_item)s.tag_id
            INNER JOIN %(model)s
                ON %(tagged_item)s.object_id = %(model_pk)s
            %%s
        WHERE %(tagged_item)s.content_type_id = %(content_type_id)s
            %%s
        GROUP BY %(tag)s.id, %(tag)s.name
        %%s
        ORDER BY %(tag)s.name ASC""" % {
            'tag': qn(Tag._meta.db_table),
            'count_sql': counts and (', COUNT(%s)' % model_pk) or '',
            'tagged_item_alias': qn(TaggedItem._meta.db_table) + " tagged_item_alias",
            'tagged_item': "tagged_item_alias",
            'model': model_table,
            'model_pk': model_pk,
            'content_type_id': ContentType.objects.get_for_model(model).pk,
        }

        min_count_sql = ''
        if min_count is not None:
            min_count_sql = 'HAVING COUNT(%s) >= %%s' % model_pk
            params.append(min_count)

        cursor = connection.cursor()

        cursor.execute(query % (extra_joins, extra_criteria, min_count_sql), params)
        tags = []
        for row in cursor.fetchall():
            t = Tag(*row[:2])
            if counts:
                t.count = row[2]
            tags.append(t)

        return tags


class Tag(TagBase):
    objects = TagManager()

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def to_dict(self):
        self_dict = {
            'id': self.pk,
            'name': self.name,
        }

        return self_dict


class ItemBase(models.Model):
    def __unicode__(self):
        return ugettext("%(object)s tagged with %(tag)s") % {
            "object": self.content_object,
            "tag": self.tag
        }

    class Meta:
        abstract = True

    @classmethod
    def tag_model(cls):
        return cls._meta.get_field_by_name("tag")[0].rel.to

    @classmethod
    def tag_relname(cls):
        return cls._meta.get_field_by_name('tag')[0].rel.related_name

    @classmethod
    def lookup_kwargs(cls, instance):
        return {
            'content_object': instance
        }

    @classmethod
    def bulk_lookup_kwargs(cls, instances):
        return {
            "content_object__in": instances,
        }


class TaggedItemBase(ItemBase):
    tag = models.ForeignKey(Tag, related_name="%(app_label)s_%(class)s_items")

    class Meta:
        abstract = True

    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return cls.tag_model().objects.filter(**{
                '%s__content_object' % cls.tag_relname(): instance
            })
        return cls.tag_model().objects.filter(**{
            '%s__content_object__isnull' % cls.tag_relname(): False
        }).distinct()


class GenericTaggedItemBase(ItemBase):
    object_id = models.IntegerField(verbose_name=_('Object id'), db_index=True)
    if django.VERSION < (1, 2):
        content_type = models.ForeignKey(
            ContentType,
            verbose_name=_('Content type'),
            related_name="%(class)s_tagged_items"
        )
    else:
        content_type = models.ForeignKey(
            ContentType,
            verbose_name=_('Content type'),
            related_name="%(app_label)s_%(class)s_tagged_items"
        )
    content_object = GenericForeignKey()

    class Meta:
        abstract=True

    @classmethod
    def lookup_kwargs(cls, instance):
        return {
            'object_id': instance.pk,
            'content_type': ContentType.objects.get_for_model(instance)
        }

    @classmethod
    def bulk_lookup_kwargs(cls, instances):
        # TODO: instances[0], can we assume there are instances.
        return {
            "object_id__in": [instance.pk for instance in instances],
            "content_type": ContentType.objects.get_for_model(instances[0]),
        }

    @classmethod
    def tags_for(cls, model, instance=None):
        ct = ContentType.objects.get_for_model(model)
        kwargs = {
            "%s__content_type" % cls.tag_relname(): ct
        }
        if instance is not None:
            kwargs["%s__object_id" % cls.tag_relname()] = instance.pk
        return cls.tag_model().objects.filter(**kwargs).distinct()


class TaggedItem(GenericTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = _("Tagged Item")
        verbose_name_plural = _("Tagged Items")
