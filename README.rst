Greenmine Backend
=================


Setup development environment.
------------------------------

.. code-block:: console

    pip install -r requirements.txt
    python manage.py syncdb --migrate --noinput
    python manage.py loaddata initial_user
    python manage.py sample_data
    python manage.py createinitialrevisions


Auth: admin/123123


Polyfill's
----------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. On ``base.__init__`` has a monky patch for this bug. On its solved on django rest framework,
this patch must be removed.
