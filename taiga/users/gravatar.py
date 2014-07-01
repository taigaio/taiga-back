import hashlib
from urllib.parse import urlencode

from django.conf import settings

from taiga.base.utils.urls import get_absolute_url


GRAVATAR_BASE_URL = "http://www.gravatar.com/avatar/{}?{}"


def get_gravatar_url(email: str, **options) -> str:
    """Get the gravatar url associated to an email.

    :param options: Additional options to gravatar.
    - `default` defines what image url to show if no gravatar exists
    - `size` defines the size of the avatar.
    By default the `settings.GRAVATAR_DEFAULT_OPTIONS` are used.

    :return: Gravatar url.
    """
    defaults = settings.GRAVATAR_DEFAULT_OPTIONS.copy()
    default = defaults.get("default", None)
    if default:
        defaults["default"] = get_absolute_url(default)
    defaults.update(options)
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    url = GRAVATAR_BASE_URL.format(email_hash, urlencode(defaults))

    return url
