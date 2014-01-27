.. _intro-overview:

========
Overview
========

Requirements
============

* python 2.6 or 2.7
* django-superview >= 0.2
* psycopg2 >= 2.4 (if postgresql is used)
* pyzmq >= 2.2 (for async mailserver)
* sphinx >= 1.1.3 (for build this documentation)
* django >= 1.4 (builtin)
* markdown >= 2.1 (for markdown wiki)
* docutils >= 0.7 (for restructuredtext wiki)

Philosophy
==========

TODO

Installing
==========

TODO

Version Check
=============

TODO

.. _runtests:

Running tests
=============

Requirements for running tests: same as standard requierements.

To run tests, open a shell on a package directory and type::
    
    python manage.py test -v2 taiga

To access coverage of tests you need to install the coverage_ package and run the tests using::
    
    coverage run --omit=extern manage.py test -v2 taiga

and to check out the coverage report::
    
    coverage html


.. _contributing:

Contributing
============

Develpment of Green-Mine happens at github: https://github.com/niwibe/Green-Mine

We very much welcome your contribution of course. To do so, simply follow these guidelines:

1. Fork ``taiga`` on github.
2. Create feature branch. Example: ``git checkout -b my_new_feature``
3. Push your changes. Example: ``git push -u origin my_new_feature``
4. Send me a pull-request.

.. _license:

License
=======

This software is licensed under the New BSD_ License. See the LICENSE
file in the top distribution directory for the full license text.

.. _coverage: http://nedbatchelder.com/code/coverage/
.. _BSD: http://www.opensource.org/licenses/bsd-license.php
