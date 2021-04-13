# -*- coding: utf-8 -*-
def tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(str.lower, instance.tags))
