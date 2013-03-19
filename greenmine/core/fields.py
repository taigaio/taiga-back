# -*- coding: utf-8 -*-
# Copyright (c) 2011 Andrei Antoukh <niwi@niwi.be>
# License: BSD-3

from django.db import models
from base64 import b64encode, b64decode

try:
    import cPickle as pickle
except ImportError:
    import pickle

import logging

logger = logging.getLogger("niwi")

class DictField(models.Field):
    """ Dictionary pickled field. """
    __metaclass__ = models.SubfieldBase
    __prefix__ = "pickle_dict::"
    __pickleproto__ = -1

    def to_python(self, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, (str, unicode)) and value.startswith(self.__prefix__):
            local_value = value[len(self.__prefix__):]
            return pickle.loads(b64decode(str(local_value)))
        else:
            return {}

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is not None:
            if isinstance(value, dict):
                value = self.__prefix__ + b64encode(pickle.dumps(value, protocol=self.__pickleproto__))
            else:
                raise TypeError('This field can only store dictionaries.')

        return value

    def get_internal_type(self):
        return 'TextField'

    def value_to_string(self, obj):
        if not obj:
            return ""

        value = getattr(obj, self.attname)
        assert isinstance(value, dict)
        return self.__prefix__ + b64encode(pickle.dumps(value, protocol=self.__pickleproto__))
        return self.token.join(map(unicode, value))

    def south_field_triple(self):
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class ListField(models.Field):
    """ Pickled list field. """
    __metaclass__ = models.SubfieldBase
    __prefix__ = "pickle_list::"
    __pickleproto__ = -1

    def to_python(self, value):
        if isinstance(value, (list,tuple)):
            return value

        if isinstance(value, (str, unicode)) and value.startswith(self.__prefix__):
            local_value = value[len(self.__prefix__):]
            return pickle.loads(b64decode(str(local_value)))
        else:
            return []

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is not None:
            if isinstance(value, (list,tuple)):
                value = self.__prefix__ + b64encode(pickle.dumps(value, protocol=self.__pickleproto__))
            else:
                raise TypeError('This field can only store list or tuple objects')

        return value

    def get_internal_type(self):
        return 'TextField'

    def value_to_string(self, obj):
        if not obj:
            return ""

        value = getattr(obj, self.attname)
        assert isinstance(value, (list, tuple))
        return self.__prefix__ + b64encode(pickle.dumps(value, protocol=self.__pickleproto__))
        return self.token.join(map(unicode, value))

    def south_field_triple(self):
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class CSVField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(CSVField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def south_field_triple(self):
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
