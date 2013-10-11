# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_wiki_page(id, owner, project, save=True):
    model = get_model("wiki", "WikiPage")

    instance = model(
       slug="wikipage-{0}".format(id),
       content="WikiPage {0}".format(id),
       project=project,
       owner=owner
    )

    if save:
        instance.save()
    return instance
