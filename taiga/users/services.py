# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

"""
This model contains a domain logic for users application.
"""

from django.db.models.loading import get_model
from django.db.models import Q
from django.conf import settings

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError

from taiga.base import exceptions as exc
from taiga.base.utils.urls import get_absolute_url

from .gravatar import get_gravatar_url


def get_and_validate_user(*, username:str, password:str) -> bool:
    """
    Check if user with username/email exists and specified
    password matchs well with existing user password.

    if user is valid,  user is returned else, corresponding
    exception is raised.
    """

    user_model = get_model("users", "User")
    qs = user_model.objects.filter(Q(username=username) |
                                   Q(email=username))
    if len(qs) == 0:
        raise exc.WrongArguments("Username or password does not matches user.")

    user = qs[0]
    if not user.check_password(password):
        raise exc.WrongArguments("Username or password does not matches user.")

    return user


def get_photo_url(photo):
    """Get a photo absolute url and the photo automatically cropped."""
    try:
        url = get_thumbnailer(photo)['avatar'].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_photo_or_gravatar_url(user):
    """Get the user's photo/gravatar url."""
    if user:
        return get_photo_url(user.photo) if user.photo else get_gravatar_url(user.email)
    return ""


def get_big_photo_url(photo):
    """Get a big photo absolute url and the photo automatically cropped."""
    try:
        url = get_thumbnailer(photo)['big-avatar'].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_big_photo_or_gravatar_url(user):
    """Get the user's big photo/gravatar url."""
    if user:
        return get_big_photo_url(user.photo) if user.photo else get_gravatar_url(user.email, size=settings.DEFAULT_BIG_AVATAR_SIZE)
    return ""
