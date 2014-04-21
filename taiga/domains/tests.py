# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from django import test
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.http import HttpResponse

from . import base
from .models import Domain
from .middleware import DomainsMiddleware


class DomainCoreTests(test.TestCase):
    fixtures = ["initial_domains.json"]

    def setUp(self):
        base.clear_domain_cache()

    @override_settings(DOMAIN_ID=1)
    def test_get_default_domain(self):
        default_domain = base.get_default_domain()
        self.assertEqual(default_domain.domain, "localhost")

    @override_settings(DOMAIN_ID=2)
    def test_get_wrong_default_domain(self):
        with self.assertRaises(ImproperlyConfigured):
            default_domain = base.get_default_domain()

    def test_get_domain_by_name(self):
        domain = base.get_domain_for_domain_name("localhost")
        self.assertEqual(domain.id, 1)
        self.assertEqual(domain.domain, "localhost")

    def test_get_domain_by_name_aliased(self):
        main_domain = base.get_default_domain()
        aliased_domain = Domain.objects.create(domain="beta.localhost", scheme="http",
                                               alias_of=main_domain)

        resolved_domain = base.get_domain_for_domain_name("beta.localhost", follow_alias=False)
        self.assertEqual(resolved_domain.domain, "beta.localhost")

        resolved_domain = base.get_domain_for_domain_name("beta.localhost", follow_alias=True)
        self.assertEqual(resolved_domain.domain, "localhost")

    def test_lru_cache_for_get_default_domain(self):
        with self.assertNumQueries(1):
            base.get_default_domain()
            base.get_default_domain()

    def test_lru_cache_for_get_domain_for_domain_name(self):
        with self.assertNumQueries(2):
            base.get_domain_for_domain_name("localhost", follow_alias=True)
            base.get_domain_for_domain_name("localhost", follow_alias=True)
            base.get_domain_for_domain_name("localhost", follow_alias=False)
            base.get_domain_for_domain_name("localhost", follow_alias=False)

    def test_activate_deactivate_domain(self):
        main_domain = base.get_default_domain()
        aliased_domain = Domain.objects.create(domain="beta.localhost", scheme="http",
                                               alias_of=main_domain)

        self.assertEqual(base.get_active_domain(), main_domain)

        base.activate(aliased_domain)
        self.assertEqual(base.get_active_domain(), aliased_domain)

        base.deactivate()
        self.assertEqual(base.get_active_domain(), main_domain)


from django.test.client import RequestFactory

class DomainMiddlewareTests(test.TestCase):
    fixtures = ["initial_domains.json"]

    def setUp(self):
        self.main_domain = base.get_default_domain()
        self.aliased_domain = Domain.objects.create(domain="beta.localhost", scheme="http",
                                                    alias_of=self.main_domain)
        self.factory = RequestFactory()

    def test_process_request(self):
        request = self.factory.get("/", HTTP_X_HOST="beta.localhost")
        middleware = DomainsMiddleware()
        ret = middleware.process_request(request)

        self.assertEqual(request.domain, self.main_domain)
        self.assertEqual(ret, None)

    def test_process_request_with_wrong_domain(self):
        request = self.factory.get("/", HTTP_X_HOST="beta2.localhost")
        middleware = DomainsMiddleware()
        ret = middleware.process_request(request)

        self.assertFalse(hasattr(request, "domain"))
        self.assertNotEqual(ret, None)
        self.assertIsInstance(ret, HttpResponse)

    def test_process_request_without_host_header(self):
        request = self.factory.get("/")
        middleware = DomainsMiddleware()
        ret = middleware.process_request(request)

        self.assertEqual(request.domain, self.main_domain)
        self.assertEqual(ret, None)
