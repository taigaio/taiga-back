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


Polyfills
----------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. The file ``greenmine/base/monkey.py`` contains a temporary fix for this bug. 

This patch is applied when the module ``base.models`` it's loaded. Once it's solved on django rest framework,this patch can be removed.
