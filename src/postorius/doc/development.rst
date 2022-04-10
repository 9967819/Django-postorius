===========
Development
===========

This is a short guide to help you get started with Postorius development.


Development Workflow
====================

The source code is hosted on GitLab_, which means that we are using
Git for version control.

.. _GitLab: https://gitlab.com/mailman/postorius

Changes are not made directly in the project's master branch, but in
feature-related personal branches, which get reviewed and then merged into
the master branch. There is a contribution guide here_, that mentions the basics
about contributing to any mailman project.

.. _here: http://wiki.list.org/DEV/HowToContributeGit

An ideal workflow would be like this:

1. File a bug to suggest a new feature or report a bug (or just pick one of
   the existing bugs).
2. Create a new branch with your code changes.
3. Make a "merge request" to get your code reviewed and merged.


First Contributions / Coverage Reports
======================================

If you don't know how you can contribute,
writing tests is a good way to get you started.

You can start by exploring the existing `test coverage`_
and finding code that's not covered ie. not tested.

.. _`test coverage`: https://mailman.gitlab.io/postorius/index.html


Installing and running the tests
================================

After checkout you can run the tests using ``tox``:

::

    $ tox

By default this will test against a couple of different environments.
If you want to only run the tests in a specific environment or a single
module, you can specify this using the ``-e`` option and/or a double
dash:

::

    # List all currently configured envs:
    $ tox -l
    py36-django22
    py36-django31
    py36-django32
    py36-django-latest
    py37-django22
    py37-django31
    py37-django32
    py37-django-latest
    py38-django22
    py38-django31
    py38-django32
    py38-django-latest
    py39-django22
    py39-django31
    py39-django32
    py39-django-latest
    py310-django22
    py310-django31
    py310-django32
    py310-django-latest

    # Test Django 3.2 on Python3.7 only:
    $ tox -e py37-django32

    # Run only tests in ``test_address_activation.py``:
    $ tox -e py37-django32-- src/postoriustests/test_address_activation.py

    # You get the idea...
    $ tox -e py37-django32 -- postorius.tests.test_address_activation


All test modules reside in the ``postorius/src/postorius/tests``
directory. Please have a look at the existing examples.


Calling Mailman's REST API
==========================

A lot of Postorius' code involves calls to Mailman's REST API (through the
``mailmanclient`` library). Postorius' test uses `pytest`_ along with
`pytest-django`_ to run tests.

Postorius uses `pytest fixtures`_ to setup Mailman Core's REST API and is
defined at ``postorius.tests.mailman_api_tests.conftest.mailman_rest_layer``. It
is set to ``autouse=True`` so, all the tests inside the module
``mailman_api_tests`` automatically use it.

``mailman_rest_layer`` starts up ``incoming`` runner and ``rest`` runner using
``mailman.testing.helpersTestableMaster``. It also removes all the data after
every ``TestCase`` class.


.. _pytest fixtures: https://docs.pytest.org/en/latest/fixture.html
.. _pytest: https://docs.pytest.org/en/latest/contents.html
.. _pytest-django: https://pytest-django.readthedocs.io/en/latest/


View Authorization
==================

Three of Django's default User roles are relevant for Postorius:

- Superuser: Can do everything.
- AnonymousUser: Can view list index and info pages.
- Authenticated users: Can view list index and info pages. Can (un)subscribe
  from lists.

Apart from these default roles, there are two others relevant in Postorius:

- List owners: Can change list settings, moderate messages and delete their
  lists.
- List moderators: Can moderate messages.

There are a number of decorators to protect views from unauthorized users.

- ``@user_passes_test(lambda u: u.is_superuser)`` (redirects to login form)
- ``@login_required`` (redirects to login form)
- ``@list_owner_required`` (returns 403 if logged-in user isn't the
  list's owner)
- ``@list_moderator_required`` (returns 403 if logged-in user isn't the
  list's moderator)


Accessing the Mailman API
=========================

Postorius uses mailmanclient to connect to Mailman's REST API. In order to
directly use the client, ``cd`` to the ``example_project`` folder and execute
``python manage.py mmclient``. This will open a python shell (IPython, if
that's available) and provide you with a client object connected to your
local Mailman API server (it uses the credentials from your settings.py).

A quick example:

::

    $ python manage.py mmclient

    >>> client
    <Client (user:pwd) http://localhost:8001/3.1/>

    >>> print(client.system['mailman_version'])
    GNU Mailman 3.0.0b2+ (Here Again)

    >>> mailman_dev = client.get_list('mailman-developers@python.org')
    >>> print(mailman_dev.settings)
    {u'description': u'Mailman development',
     u'default_nonmember_action': u'hold', ...}

For detailed information how to use mailmanclient, check out its documentation_.

.. _documentation: http://docs.mailman3.org/projects/mailmanclient/en/latest/using.html
