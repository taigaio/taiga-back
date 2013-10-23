Greenmine Backend
=================

.. image:: http://kaleidos.net/static/img/badge.png
    :target: http://kaleidos.net/community/greenmine/

.. image:: https://travis-ci.org/kaleidos/greenmine-back.png?branch=master
    :target: https://travis-ci.org/kaleidos/greenmine-back

.. image:: https://coveralls.io/repos/kaleidos/greenmine-back/badge.png?branch=master
    :target: https://coveralls.io/r/kaleidos/greenmine-back?branch=master


Setup development environment
-----------------------------

Just execute these commands in your virtualenv(wrapper):

.. code-block:: console

    pip install -r requirements.txt
    python manage.py syncdb --migrate --noinput
    python manage.py loaddata initial_user
    python manage.py sample_data
    python manage.py createinitialrevisions


Note: greenmine only runs with python 3.3+.

Note: Initial auth data: admin/123123


Polyfills
---------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. The file ``greenmine/base/monkey.py`` contains a temporary fix for this bug.

This patch is applied when the module ``base.models`` it's loaded. Once it's solved on django rest
framework, this patch can be removed.
