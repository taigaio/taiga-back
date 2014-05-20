from django.db.models import signals


def disconnect_signals():
    signals.pre_save.receivers = []
    signals.post_save.receivers = []


def pytest_runtest_setup(item):
    disconnect_signals()
