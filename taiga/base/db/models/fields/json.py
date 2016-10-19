# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import JSONField as DjangoJSONField

# NOTE: After upgrade Django to the future release (1.11) change
#           class JSONField(FutureDjangoJSONField):
#       to
#           class JSONField(DjangoJSONField):
#       and remove the classes JsonAdapter and FutureDjangoJSONField

import json
from psycopg2.extras import Json
from django.core import exceptions


class JsonAdapter(Json):
    """
    Customized psycopg2.extras.Json to allow for a custom encoder.
    """
    def __init__(self, adapted, dumps=None, encoder=None):
        self.encoder = encoder
        super().__init__(adapted, dumps=dumps)

    def dumps(self, obj):
        options = {'cls': self.encoder} if self.encoder else {}
        return json.dumps(obj, **options)


class FutureDjangoJSONField(DjangoJSONField):
    def __init__(self, verbose_name=None, name=None, encoder=None, **kwargs):
        if encoder and not callable(encoder):
            raise ValueError("The encoder parameter must be a callable object.")
        self.encoder = encoder
        super().__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.encoder is not None:
            kwargs['encoder'] = self.encoder
        return name, path, args, kwargs

    def get_prep_value(self, value):
        if value is not None:
            return JsonAdapter(value, encoder=self.encoder)
        return value

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        options = {'cls': self.encoder} if self.encoder else {}
        try:
            json.dumps(value, **options)
        except TypeError:
            raise exceptions.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )


__all__ = ["JSONField"]

class JSONField(FutureDjangoJSONField):
    def __init__(self, verbose_name=None, name=None, encoder=DjangoJSONEncoder, **kwargs):
        super().__init__(verbose_name, name, encoder, **kwargs)
