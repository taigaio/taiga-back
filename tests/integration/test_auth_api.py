from unittest import mock
import pytest

from django.core.urlresolvers import reverse

from .. import factories

pytestmark = pytest.mark.django_db


def setup_module(module):
    module.patcher = mock.patch("taiga.domains.base.get_default_domain",
                                mock.Mock(return_value=factories.DomainFactory()))
    module.patcher.start()

def teardown_module(module):
    module.patcher.stop()


class TestPublicRegistration:
    @classmethod
    def setup_class(cls):
        cls.form = {"username": "username", "password": "password", "first_name": "fname",
                    "last_name": "lname", "email": "user@email.com", "type": "public"}

    def test_respond_201_if_domain_allows_public_registration(self, client):
        domain = factories.DomainFactory(public_register=True)
        response = client.post(reverse("auth-register"), self.form, HTTP_X_HOST=domain.domain)
        assert response.status_code == 201

    def test_respond_400_if_domain_does_not_allow_public_registration(self, client):
        domain = factories.DomainFactory(public_register=False)
        response = client.post(reverse("auth-register"), self.form, HTTP_X_HOST=domain.domain)
        assert response.status_code == 400


@pytest.mark.xfail
class TestPrivateRegistration:
    @classmethod
    def setup_class(cls):
        cls.form = {"username": "username", "password": "password", "first_name": "fname",
                    "last_name": "lname", "email": "user@email.com", "type": "private",
                    "existing": "1"}

    def test_respond_201_if_domain_allows_public_registration(self, client):
        domain = factories.DomainFactory(public_register=True)
        membership = factories.MembershipFactory()
        headers = {"HTTP_X_HOST": domain.domain}
        response = client.post(reverse("auth-register"), self.form, **headers)
        assert response.status_code == 201
