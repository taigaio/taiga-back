import hashlib

from taiga.users.gravatar import get_gravatar_url


def test_get_gravatar_url():
    email = "user@email.com"
    email_hash = hashlib.md5(email.encode()).hexdigest()
    url = get_gravatar_url(email, s=40, d="default-image-url")

    assert email_hash in url
    assert 's=40' in url
    assert 'd=default-image-url' in url
