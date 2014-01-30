Taiga Backend
=================

.. image:: http://kaleidos.net/static/img/badge.png
    :target: http://kaleidos.net/community/taiga/

.. image:: https://travis-ci.org/taigaio/taiga-back.png?branch=master
    :target: https://travis-ci.org/taigaio/taiga-back

.. image:: https://coveralls.io/repos/taigaio/taiga-back/badge.png?branch=master
    :target: https://coveralls.io/r/taigaio/taiga-back?branch=master



Setup development environment
-----------------------------

Just execute these commands in your virtualenv(wrapper):

.. code-block:: console

    pip install -r requirements.txt
    python manage.py migrate --noinput
    python manage.py loaddata initial_user
    python manage.py loaddata initial_project_templates
    python manage.py loaddata initial_role
    python manage.py sample_data


Note: taiga only runs with python 3.3+.

Note: Initial auth data: admin/123123


Polyfills
---------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. The file ``taiga/base/monkey.py`` contains a temporary fix for this bug.

This patch is applied when the module ``base.models`` it's loaded. Once it's solved on django rest
framework, this patch can be removed.
