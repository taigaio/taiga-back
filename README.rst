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

You have to load the sql sentences of the file ``sql/tags.sql`` and your database
must support PL/Python. You use a dbuser with privileges in the database,
'greenmine' for example, to do this.

.. code-block:: console

    psql greenmine

.. code-block:: sql

    CREATE LANGUAGE plpythonu;

    CREATE OR REPLACE FUNCTION unpickle (data text)
        RETURNS text[]
    AS $$
        import base64
        import pickle

        return pickle.loads(base64.b64decode(data))
    $$ LANGUAGE plpythonu IMMUTABLE;

    CREATE INDEX issues_unpickle_tags_index ON issues_issue USING btree (unpickle(tags));


Note: greenmine only runs with python 3.3+.

Note: Initial auth data: admin/123123


Polyfills
---------

Django-Rest Framework by default returns 403 for not authenticated requests and permission denied
requests. The file ``greenmine/base/monkey.py`` contains a temporary fix for this bug.

This patch is applied when the module ``base.models`` it's loaded. Once it's solved on django rest
framework, this patch can be removed.
