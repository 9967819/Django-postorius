================
News / Changelog
================

The Postorius Django app provides a web user interface to
access GNU Mailman.

Postorius is free software: you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3 of the License.

Postorius is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Postorius. If not, see <http://www.gnu.org/licenses/>.


.. _NEWS-1.3.6:

1.3.6
=====

(2021-09-28)

UI
--

* Add 'Delivery Mode' and 'Moderation Action' columns to List members
  page. (See #471)
* Add support to list and handle pending un-subscription requests. (Closes
  #332)
* Add support to specify a reason when handling (un)subscription requests
  (Closes #450)
* Success messages to mass subscribes now properly distinguish subscription
  from invitation and indicate possible pending confirmation or approval.
  (Closes #481)
* User profile dropdown no longer is too far right.  (Closes #486)
* Expose ``archive_rendering_mode`` in Archiver settings to choose between
  plaintext and rich text rendering of emails in Hyperkitty. (Closes #487)
* Allow choosing ``delivery_mode`` and ``delivery_status`` when subscribing to
  a List. (Closes #488)
* Redirect to ``domain_index`` after ``domain_edit`` succeeds. (Closes
  #428)
* Expose new ``bounce_notify_owner_on_bounce_increment`` list setting on
  ``Bounce Processing`` settings, and expose the corresponding template.
* Expose the ``forward_unrecognized_bounces_to`` setting on
  ``Bounce Processing`` settings.
* Clarified the description of ``Maximum number of recipients``.  (Closes #515)
* List summary view will now display a table for all subscriptions with
  ``delivery_mode`` and ``delivery_status``. (Closes #470)
* Add a new user management interface for superusrs. (See #518)
* Allow searching for users in list user views. (See #518)
* Show both display name and email in user management interface if available,
  (See #518)
* Allow ``list:admin:notice:pending`` template to be set in Postorius. (Closes
  #526)

Other
-----

* Use mass-subscription API in core for Mass Removal of Members. (Closes #464)
* Fix a bug where users with multiple subscriptions to a List couldn't view
  their Preferences for all addresses. (Closes #472)
* Check for pending unsubscription requests and notify user when the request is
  pending approval. (Closes #473)
* Improve the performance of Members' page by skipping an API call. (Closes
  #483)
* Improve the performance of List index page for Superuser. (See !599)
* Skip looking up choosable_domains for non-superuser to reduce API calls. (See
  !600)
* Improve the performance of List owner access checks. (See !598)
* Add a new ``APICountingMiddleware`` to performance testing purposes. (See
  !604)
* Use ``user_id`` as ``subscriber`` instead of addresses to improve the
  efficiency of list index page. (Closes #419)
* ``AUTOCREATE_MAILMAN_USER`` setting is now removed and a Mailman user is
  always created when a User object in created in Django. Also remove duplicate
  implementation of ``get_mailman_user`` from ``MailmanUserManager`` so that we
  can use a single implementation that uses caching for efficient lookups.
* Bump bundled jQuery to 3.6.0.slim version. (See !637)
* Use the full jQuery not the slim version. (Closes #523)
* Do not show Ownerships and Moderator roles in the 'Subscriptions' page
  under mange new user interface. (Closes #534)

Ascessibility
-------------
* Move the focus to the textarea in mass subscribe page if there are errors in
  the form. (Closes #493)


.. _news-1.3.5:

1.3.5
=====

(2021-09-05)

* ``AUTOCREATE_MAILMAN_USER`` setting is now removed and a Mailman user is
  always created when a User object in created in Django. Also remove duplicate
  implementation of ``get_mailman_user`` from ``MailmanUserManager`` so that we
  can use a single implementation that uses caching for efficient lookups.

Security
--------
* Check that a user owns the email address they are trying to unsubscribe. This
  fixes a bug in which any logged-in user could unsubscribe any email address
  from any mailing list, leaking whether that address was subscribed originally.
  (CVE-2021-40347, Closes #531)

  
.. _news-1.3.4:

1.3.4
=====

(2021-02-02)

* Update the default Site when creating a domain to match the domain if it is
  ``example.com``. (Closes #427)
* Add the ability to subscribe via Primary Address instead of specific
  address. (See !516)
* Fix a bug where the user's display name would be ignore when
  subscribing. (Closes #429)
* Display a user's name in the pending subscription request list. (Closes #430)
* Set a user's preferrred_address in Core if it isn't already set and the user
  has a Primary Address that is verified.
* Use the new APIs in Core to get the count of held messages and pending
  subscriptions to improve peroformance of settings page for list
  owners. (Fixes #417)
* Show held message is local time of the User. (Closes #434)
* Fix a bug where non-member options page would show an owner's options if the
  same email was subscribed as owner and non-member in a list. (Closes #436)
* Switching subscription from one email address to other or Primary Address now
  preserves preferences and does not require Moderator approval. (Closes #425)
* Make 'Archives' and 'List Options' urls more prominently visible in the
  list summary page as buttons. (Closes #439)
* Added the ability to issue invitations from the mass subscribe view.
* Expose ``emergency`` moderation setting for MailingList.
* Fixed some minor HTML errors. (Closes #442)
* Fix the bug where ListOfStringsField couldn't be unset in Postorius. (Closes
  #444)
* Allow ``list:user:action:invite`` template to be set in Postorius. (Closes
  #454)
* Fix a bug where the Bans form would always use default language instead of
  current request's language. (Closes #441)
* Fix the URL on cancel buttons in template's confirm delete page. (Closes
  #458)
* Use server side filtering for pending subscription requests for moderator
  approval. (See !559)
* Allow setting moderation action for a nonmember from Held Message modal. (
  Closes #448)
* Add a new view to confirm subscriptions or new emails for Users using
  Postorius. (Fixes #459)
* Fix a bug where membership check compared email addresses in different
  cases. (Closes #457)
* Mass removal now accepts address formats with display names and/or angle
  brackets. (Closes #455)
* Add support to override ``send_welcome_message`` when mass subscribing to
  suppress welcome messages. (Closes #99)
* Add support for Django 3.1.x. (See !574)
* The list's ``send_goodbye_message`` is now settable on the Automatic
  Responses view.  (Closes #466)
* Support ``HYPERKITTY_ENABLE_GRAVATAR`` setting to control the user gravatar.
  (Closes #467)

.. _news-1.3.3:

1.3.3
=====

(2020-06-01)

* Expose additional list settings.  (See !483)
* Correct description of Digest Frequency.  (Closes #395)
* Added links to Reply-To munging articles.  (Closes #401)
* Fix "Show Headers" button to show the held message headers in the
  held message popup. (Closes #407)
* Fix the held message popup structure and increase the max width of the popup
  to be 800px(modal-lg) for larger screens. (Closes #405)
* Fix FILTER_VHOST = True option to try to find the email host corresponding
  to the requesting web host.  (Closes #394)
* Allow specifying a reason when rejecting a held message. (Closes #412)
* Allow users to set their preferred language in their preferences. (Closes #413)
* Add support to ban addresses for the entire Mailman installation. (Closes #357)
* Un-handled ``HTTPError`` exception raised from MailmanClient now results in an
  error page and proper logging instead of mysterious ``KeyError`` in logs.
  (Closes #341)
* Change List settings navigation to be vertical instead of horizontal. (See
  !509)
* Move bounce processing settings into a new vertical tab for better
  visibility.
* Add URL to edit the Web host for each domain in Domain Index page. Also, show
  the ``SITE_ID`` for each webhost. (Closes #426)


1.3.2
=====

(2020-01-12)

* Do not show pagination, when user is authenticated. (Closes #387)
* Drop support for Django 1.11.
* Add support to choose options for ``pre_confirm``, ``pre_approve`` and
  ``pre_verify`` when mass subscribing. (Fixes #203)

1.3.1
=====

(2019-12-08)

* Show templates' file names in selection list where admins can pick
  individual templates for customization. (See !425)
* Make template short names more prominent on all email templates related
  views. (See !425)
* Bind object attributes to local variables in {% blocktrans %} (See !439)
* Set the initial style in new list form as the default style. (Closes #310)
* Fix a bug where logged in users's index page view would cap the total number
  of lists for a role to 50. (Closes #335)
* Fix a bug where handling non-existent held message can raise 500
  exception. (Closes #349)
* Emit appropriate signals when Domain and MailingList is updated. (Closes
  #385)
* Do not strip leading whitespaces in Email Templates. (Closes #301)
* Hold date for held messages are now displayed correctly. (Closes #312)
* Add support for Python 3.8.
* Add support for Django 3.0.

1.3.0
=====

(2019-09-04)

* Fix a string substitution bug which would cause un-substituted raw string to
  be exposed as notification to admin. (Closes #327)
* Add support for ``FILTER_VHOST`` option to filter MalingLists based on
  ``HOST`` header of incoming request. (Closes #330)
* List Summary page now renders List info as markdown. (Closes #244)
* Moderation action for held message's sender can now be set from held
  message's view.(Closes #127)
* Add a 'Ban' button to list of subscription requests to help administrators
  against spams. (Closes #339)
* Added support for Django 2.2.
* ``pytest`` will be used to run tests instead of default Django's test runner.
* Remove ``vcrpy`` and use fixtures to start and stop Mailman's REST API to
  test against, without having to record tapes to be replayed.
* Corrected display message in 'recieve_list_copy' option in global mailman
  preferences of mailman settings. (Closes #351)
* Allow setting a MailingList's Preferred Language. (Closes #303)
* Allow a empty templates as a workaround for missing settings to skip
  email decoration. (Closes #331)
* Expose ``digest_volume_frequency``, ``digest_send_periodict`` and
  ``digests_enabled`` settings for MailingLists.
* Add a badge with count of held messages and pending subscription requests
  for moderator approval. (Closes #308)
* Add support to add, view and remove domain owners.
* Allow setting the visibility options for MailingList's member list.
* Make page titles localizable.


1.2.4
=====
(2019-02-09)

* Add support for ``explicit_header_only`` in list settings.
  (See !369)


1.2.3
=====
(2019-01-19)

* Expose ``max_num_recipients`` in list settings.  (Closes #297)
* Add support for Non-member management in Postorius.  (Closes #265)
* ``Members`` tab in Mailing List settings page is now called ``Users``.
  (Closes #309)
* Show pending subscription requests are only pending for Moderator.
  (Closes #314)


1.2.2
=====
(2018-08-30)

* Add support for Python 3.7 with Django 2.0+
* Index page only shows related lists for signed-in users with option to
  filter based on role.
* Expose respond_to_post_requests in Postorius. (Closes #223)


1.2.1
=====
(2018-07-11)

* A Django migration was missing from version 1.2.0.  This is now added.

1.2
===
(2018-07-10)

* Postorius now runs only on Python 3.4+ and supports Django 1.8 and 1.11+
* Added the ability to set and edit ``alias_domain`` to the ``domains`` forms.
* List Create form now allows selecting the ``style``. A ``style`` is how a new
  mailing list is configured.
* Minimum supported Mailman Core version is now 3.2.0. This is because the
  ``styles`` attribute for MailingList resource is exposed in 3.2, which
  contains all the default ``styles`` supported by Core and their human readable
  description.
* Account subscription page now lists all the memberships with their respective
  roles. This avoids repeated API calls for the way data was displayed
  before.  (Closes #205)
* Postorius now supports only Django 1.11+.
* Duplicate MailingList names doesn't return a 500 error page and instead adds
  an error to the New MailingList  form. (Fixes #237)
* Pending subscription requests page is now paginated. (See !298)
* Add owners/moderators form now allows specifying a Display Name, along with
  their email. (Fixes #254)
* Members views now show total number of members at the top. (See !315)
* Fixed a bug where GET on views that only expect a POST would cause 500 server
  errors instead of 405 method not allowed. (Fixes #185)
* Member preferences form can now be saved without having to change all the
  fields. (Fixes #178)
* Fixed a bug where the 'Delete' button to remove list owners didn't work due to
  wrong URL being rendered in the templates. (Fixes #274)
* Require Explicit Destination is added to the Message Acceptance form.
  (Closes #277)
* Delete Domain page now shows some extra warning information about all the
  mailing lists that would be deleted after deleting the Domain. (See !250)
* Superusers can now view Mailman Core's current version and REST API version
  being used under 'System Information' menu in the top navigation bar. (See !325)
* Fixed a bug where 500 error template wouldn't render properly due to missing
  context variables in views that render that templates (See !334)
* Postorius now allows adding and editing templates for email headers, footers
  and some of the automatic responses sent out by Mailman. (See !327)

1.1.2
=====
(2017-12-27)

* Added a new ``reset_passwords`` command that resets _all_ user's passwords
  inside of Core. This password is different from the one Postorius
  maintains. The Postorius password is the one used for logging users in.
* Postorius now sets the 'Display Name' of the user in Core correctly. This
  fixes a security vulnerability where user's display_name would be set as their
  Core's password.


1.1.1
=====
(2017-11-17)

* Improved testing and internal bug fixes.
* Preserve formatting of Mailing List description in the summary view.
* Site's Name isn't capitalized anymore in the navigation bar.
* html5shiv and response.js libraries are now included, instead of loading from a CDN.

1.1.0 -- "Welcome to This World"
================================
(2017-05-26)

* Added DMARC mitigation settings
* Switch to Allauth auth library
* Preference page improvements
* Moderation page improvements
* Django support up to Django 1.11
* Added form to edit header matches
* Domain edit form improvements
* All pipelines recognized in alter messages form
* Use django-mailman3 to share common code with HyperKitty
* Various bug fixes, code cleanup, and performance improvements


1.0.3
=====
(2016-02-03)

* Fix security issue


1.0.2
=====
(2015-11-14)

* Bug fix release


1.0.1
=====
(2015-04-28)

* Help texts Small visual alignment fix; removed unnecessary links to
  separate help pages.
* Import fix in fieldset_forms module (Django1.6 only)


1.0.0 -- "Frizzle Fry"
======================
(2015-04-17)

* French translation. Provided by Guillaume Libersat
* Addedd an improved test harness using WebTest. Contributed by Aurélien Bompard.
* Show error message in login view. Contributed by Aurélien Bompard (LP: 1094829).
* Fix adding the a list owner on list creation. Contributed by Aurélien Bompard (LP: 1175967).
* Fix untranslatable template strings. Contributed by Sumana Harihareswara (LP: 1157947).
* Fix wrong labels in metrics template. Contributed by Sumana Harihareswara (LP: 1409033).
* URLs now contain the list-id instead of the fqdn_listname. Contributed by Abhilash Raj (LP: 1201150).
* Fix small bug moderator/owner forms on list members page. Contributed by Pranjal Yadav (LP: 1308219).
* Fix broken translation string on the login page. Contributed by Pranjal Yadav.
* Show held message details in a modal window. Contributed by Abhilash Raj (LP: 1004049).
* Rework of internal testing
* Mozilla Persona integration: switch from django-social-auto to django-browserid: Contributed by Abhilash Raj.
* Fix manage.py mmclient command for non-IPython shells. Contributed by Ankush Sharma (LP: 1428169).
* Added archiver options: Site-wide enabled archivers can not be enabled
  on a per-list basis through the web UI.
* Added functionality to choose or switch subscription addresses. Contributed by Abhilash Raj.
* Added subscription moderation, pre_verification/_confirmation.
* Several style changes.


1.0 beta 1 -- "Year of the Parrot"
==================================
(2014-04-22)

* fixed pip install (missing MANIFEST) (LP: 1307624). Contributed by Aurélien Bompard
* list owners: edit member preferences
* users: add multiple email addresses
* list info: show only subscribe or unsubscribe button. Contributed by Bhargav Golla
* remove members/owners/moderator. Contributed by Abhilash Raj


1.0 alpha 2 -- "Is It Luck?"
============================
(2014-03-15)

* dev setup fix for Django 1.4 contributed by Rohan Jain
* missing csrf tokens in templates contributed by Richard Wackerbarth (LP: 996658)
* moderation: fixed typo in success message call
* installation documentation for Apache/mod_wsgi
* moved project files to separate branch
* show error message if connection to Mailman API fails
* added list members view
* added developer documentation
* added test helper utils
* all code now conform to PEP8
* themes: removed obsolete MAILMAN_THEME settings from templates, contexts, file structure; contributed by Richard Wackerbarth (LP: 1043258)
* added access control for list owners and moderators
* added a mailmanclient shell to use as a ``manage.py`` command (``python manage.py mmclient``)
* use "url from future" template tag in all templates. Contributed by Richard Wackerbarth.
* added "new user" form. Contributed by George Chatzisofroniou.
* added user subscription page
* added decorator to allow login via http basic auth (to allow non-browser clients to use API views)
* added api view for list index
* several changes regarding style and navigation structure
* updated to jQuery 1.8. Contributed by Richard Wackerbarth.
* added a favicon. Contributed by Richard Wackerbarth.
* renamed some menu items. Contributed by Richard Wackerbarth.
* changed static file inclusion. Contributed by Richard Wackerbarth.
* added delete domain feature.
* url conf refactoring. Contributed by Richard Wackerbarth.
* added user deletion feature. Contributed by Varun Sharma.



1.0 alpha 1 -- "Space Farm"
===========================
(2012-03-23)

Many thanks go out to Anna Senarclens de Grancy and Benedict Stein for
developing the initial versions of this Django app during the Google Summer of
Code 2010 and 2011.

* add/remove/edit mailing lists
* edit list settings
* show all mailing lists on server
* subscribe/unsubscribe/mass subscribe mailing lists
* add/remove domains
* show basic list info and metrics
* login using django user account or using BrowserID
* show basic user profile
* accept/discard/reject/defer messages
* Implementation of Django Messages contributed by Benedict Stein (LP: #920084)
* Dependency check in setup.py contributed by Daniel Mizyrycki
* Proper processing of acceptable aliases in list settings form contributed by
  Daniel Mizyrycki
