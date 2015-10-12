# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

# This code is partially taken from django-rest-framework:
# Copyright (c) 2011-2014, Tom Christie

VERSION = "2.3.13-taiga" # Based on django-resframework 2.3.13

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = 'iso-8859-1'

# Default datetime input and output formats
ISO_8601 = 'iso-8601'


from .viewsets import ModelListViewSet
from .viewsets import ModelCrudViewSet
from .viewsets import ModelUpdateRetrieveViewSet
from .viewsets import GenericViewSet
from .viewsets import ReadOnlyListViewSet
from .viewsets import ModelRetrieveViewSet

__all__ = ["ModelCrudViewSet",
           "ModelListViewSet",
           "ModelUpdateRetrieveViewSet",
           "GenericViewSet",
           "ReadOnlyListViewSet",
           "ModelRetrieveViewSet"]
