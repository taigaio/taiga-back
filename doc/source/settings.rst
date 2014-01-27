Settings introduced by taiga.
=============================

Default settings
----------------

The setting instance contains few default parameters used in throughout
the library. This parameters can be changed by the user by simply
overriding them.

.. attribute:: settings.HOST

    Set a full host name, this is used for making urls for email 
    notifications. In the future, it will be automatic.

    Default: ``"http://localhost:8000"`` (ready for developers)

.. attribute:: settings.DISABLE_REGISTRATION

    Set this, disables user registration.

    Default: ``False``
