Greenmine Backend
=================

Setup development environment.
------------------------------

You need to install django 1.6,...

.. code-block:: console

    git clone git://github.com/django/django.git django-trunk
    cd django-trunk
    git checkout stable/1.6.x
    python setup.py install
    cd ..
    rm -r django-trunk

... django-reversion for django 1.6 ...

.. code-block:: console

    git clone https://github.com/etianen/django-reversion.git django-reversion-trunk
    cd django-reversion-trunk
    git checkout django-1.6
    python setup.py install
    cd ..
    rm -r django-reversion-trunk


...ant then, you must install all the dependencies

.. code-block:: console

    pip install -r requirements.txt
    python manage.py syncdb --migrate --noinput
    python manage.py loaddata initial_user
    python manage.py sample_data
    python manage.py createinitialrevisions

Also, greenmine only runs over python 3.3+.


Auth: admin/123123


Polyfills
----------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. The file ``greenmine/base/monkey.py`` contains a temporary fix for this bug.

This patch is applied when the module ``base.models`` it's loaded. Once it's solved on django rest
framework, this patch can be removed.
