Greenmine Backend
=================


Setup development environment.
------------------------------

.. code-block:: console

    pip install -r requirements.txt
    python manage.py syncdb --migrate --noinput
    python manage.py loaddata initial_user
    python manage.py sample_data
