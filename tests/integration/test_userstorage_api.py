import pytest

from rest_framework.reverse import reverse

from .. import factories

import json


pytestmark = pytest.mark.django_db


class TestListStorageEntries:
    def _load_initial_data(self):
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.storage11 = factories.StorageEntryFactory(owner=self.user1)
        self.storage12 = factories.StorageEntryFactory(owner=self.user1)
        self.storage13 = factories.StorageEntryFactory(owner=self.user1)
        self.storage21 = factories.StorageEntryFactory(owner=self.user2)

    def test_list_by_anonymous_user(self, client):
        self._load_initial_data()
        response = client.get(reverse("user-storage-list"))
        assert response.status_code == 401

    def test_list_only_user1_entriees(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.get(reverse("user-storage-list"))
        assert response.status_code == 200
        entries = response.data
        assert len(entries) == 3
        response = client.logout()

    def test_list_only_user2_entriees(self, client):
        self._load_initial_data()
        response = client.login(username=self.user2.username, password=self.user2.username)
        response = client.get(reverse("user-storage-list"))
        assert response.status_code == 200
        entries = response.data
        assert len(entries) == 1
        response = client.logout()

    def test_list_only_user1_entriees_filter_by_keys(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        keys = "{},{}".format(self.storage11.key, self.storage13.key)
        response = client.get("{}?keys={}".format(reverse("user-storage-list"), keys))
        assert response.status_code == 200
        entries = response.data
        assert len(entries) == 2
        response = client.logout()


class TestViewStorageEntries:
    def _load_initial_data(self):
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.storage11 = factories.StorageEntryFactory(owner=self.user1)

    def test_view_an_entry_by_anonymous_user(self, client):
        self._load_initial_data()
        response = client.get(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 401

    def test_view_an_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.get(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 200
        entry = response.data
        assert entry["key"] == self.storage11.key
        assert entry["value"] == self.storage11.value
        response = client.logout()

    def test_view_an_entry_by_incorrect_user(self, client):
        self._load_initial_data()
        response = client.login(username=self.user2.username, password=self.user2.username)
        response = client.get(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 404
        response = client.logout()

    def test_view_non_existent_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.get(reverse("user-storage-detail", args=["foo"]))
        assert response.status_code == 404
        response = client.logout()


class TestCreateStorageEntries:
    @classmethod
    def setup_class(cls):
        cls.form = {"key": "foo",
                    "value": "bar"}
        cls.form_without_key = {"value": "bar"}
        cls.form_without_value = {"key": "foo"}

    def _load_initial_data(self):
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.storage11 = factories.StorageEntryFactory(owner=self.user1)

    def test_create_entry_by_anonymous_user_with_error(self, client):
        self._load_initial_data()
        response = client.post(reverse("user-storage-list"), self.form)
        assert response.status_code == 401

    def test_create_entry_successfully(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.post(reverse("user-storage-list"), self.form)
        assert response.status_code == 201
        response = client.get(reverse("user-storage-detail", args=[self.form["key"]]))
        assert response.status_code == 200
        response = client.logout()

    def test_create_entry_with_incorret_form_error(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.post(reverse("user-storage-list"), self.form_without_key)
        assert response.status_code == 400
        response = client.post(reverse("user-storage-list"), self.form_without_value)
        assert response.status_code == 400
        response = client.logout()

    def test_create_entry_with_integrity_error(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        error_form = {"key": self.storage11.key,
                      "value": "bar"}
        response = client.post(reverse("user-storage-list"), error_form)
        assert response.status_code == 400
        response = client.logout()


class TestUpdateStorageEntries:
    @classmethod
    def setup_class(cls):
        cls.form = {"value": "bar"}

    def _load_initial_data(self):
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.storage11 = factories.StorageEntryFactory(owner=self.user1)

    def test_update_entry_by_anonymous_user(self, client):
        self._load_initial_data()
        self.form["key"] = self.storage11.key
        response = client.put(reverse("user-storage-detail", args=[self.storage11.key]),
                              json.dumps(self.form),
                              content_type='application/json')
        assert response.status_code == 401

    def test_update_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        self.form["key"] = self.storage11.key
        response = client.put(reverse("user-storage-detail", args=[self.storage11.key]),
                              json.dumps(self.form),
                              content_type='application/json')
        assert response.status_code == 200
        response = client.get(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 200
        entry = response.data
        assert entry["value"] == self.form["value"]
        response = client.logout()

    def test_update_non_existent_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        self.form["key"] = "foo"
        response = client.get(reverse("user-storage-detail", args=[self.form["key"]]))
        assert response.status_code == 404
        response = client.put(reverse("user-storage-detail", args=[self.form["key"]]),
                              json.dumps(self.form),
                              content_type='application/json')
        assert response.status_code == 201
        response = client.get(reverse("user-storage-detail", args=[self.form["key"]]))
        assert response.status_code == 200
        entry = response.data
        assert entry["value"] == self.form["value"]
        response = client.logout()


class TestDeleteStorageEntries:
    def _load_initial_data(self):
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.storage11 = factories.StorageEntryFactory(owner=self.user1)

    def test_delete_entry_by_anonymous_user(self, client):
        self._load_initial_data()
        response = client.delete(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 401

    def test_delete_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        key = self.storage11.key
        response = client.delete(reverse("user-storage-detail", args=[key]))
        assert response.status_code == 204
        response = client.get(reverse("user-storage-detail", args=[key]))
        assert response.status_code == 404
        response = client.logout()

    def test_delete_entry_by_incorrect_user(self, client):
        self._load_initial_data()
        response = client.login(username=self.user2.username, password=self.user2.username)
        response = client.delete(reverse("user-storage-detail", args=[self.storage11.key]))
        assert response.status_code == 404
        response = client.logout()

    def test_delete_non_existent_entry(self, client):
        self._load_initial_data()
        response = client.login(username=self.user1.username, password=self.user1.username)
        response = client.delete(reverse("user-storage-detail", args=["foo"]))
        assert response.status_code == 404
        response = client.logout()
