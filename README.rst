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

*Taiga only runs with Python 3.3+.*

Just execute these commands in your virtualenv(wrapper):

.. code-block:: console

    pip install -r requirements.txt
    python manage.py migrate --noinput
    python manage.py loaddata initial_user
    python manage.py loaddata initial_project_templates
    python manage.py loaddata initial_role
    python manage.py sample_data


Initial auth data: admin/123123

If you want a complete environment for production usage, you can try the taiga bootstrapping
scripts https://github.com/taigaio/taiga-scripts (warning: alpha state)

Configuration
-------------

Configuration is on the `taiga-back/settings/local.py` file.

After modifing the configuration, you have to restart taiga-back.
