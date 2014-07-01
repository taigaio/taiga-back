import hashlib
from urllib.parse import urlencode

from django.conf import settings

GRAVATAR_BASE_URL = "http://www.gravatar.com/avatar/{}?{}"


def get_gravatar_url(email: str, **options) -> str:
    """Get the gravatar url associated to an email.

    :param options: Additional options to gravatar:
    - `d` defines what image url to show if no gravatar exists
    - `s` defines the size of the avatar.
    By default these options are:
    - `d` is `settings.DEFAULT_AVATAR_URL`
    - `s` gravatar's default value which is 80x80 px

    :return: Gravatar url.
    """
    defaults = {'d': settings.DEFAULT_AVATAR_URL}
    defaults.update(options)
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    url = GRAVATAR_BASE_URL.format(email_hash, urlencode(defaults))

    return url
