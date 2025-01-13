# Changelog

## 6.8.3 (unreleased)

- ...

## 6.8.2 (2025-01-13)

- Fix: Error on load_dump when JSON is a list.

## 6.8.1 (2024-07-23)

- Changes to queries to improve their performance.
- Fix: webhooks error.
- Fix: multiple object returned on neighbour.
- Update locales.

## 6.8.0 (2024-04-03)

- Changed the namespace of the repositories, from kaleidos-ventures to taigaio
- Fix SECURE_PROXY_SSL_HEADER, adjust header name to match standard (thanks [@ChriFo](https://github.com/ChriFo))
- Fix error appliying migrations: "resource module not found" (thanks [@VirajAdiga](https://github.com/VirajAdiga))
- Allow to disable the use of server-side cursors to support pgbouncer (thanks [@ordinary-dev](https://github.com/ordinary-dev))
- Inmproved RabbitMQ host configuration for Taiga events and asynchrous tasks (thanks [@iriseden](https://github.com/iriseden))
- Make options for webhooks configurable via env vars in docker (thanks [@slakner](https://github.com/slakner))

## 6.7.3 (2024-02-21)

- GitHub Importer: fix import error with issues associated to a closed milestone.
- Trello Importer: fix import error with attachemts without owner.
- Trello Importer: fix import error when attachemt name ends with '/'.
- User Story Report: add epic refs.

## 6.7.2 (2024-02-16)

- Docker: DEBUG and LANGUAGE_CODE settings are customizable.

## 6.7.1 (2023-09-20)

- Upgrade gitlab auth contrib plugin
- Set celery timezone customizable from docker envs (thanks to [@wowi42](https://github.com/wowi42))
- Fix some typos in comments syntax in settings files (thanks to [@Ser5](https://github.com/Ser5))

## 6.7.0 (2023-06-12)

- Security improvements to webhooks functionality.
- Make migrations compatible with Postgresql-14

## 6.6.2 (2023-03-24)

- Fix queries related to telemetry service.

## 6.6.1 (2023-03-13)

- Fix error generating the front sitemaps.xml files

## 6.6.0 (2023-03-06)

- Add support for Python 3.11
- Remove support for Python 3.7
- Upgrade to Django 3.2 (and upgrade some other dependencies)
- Fix some silent css error in email templates (thanks to [@sarbanha](https://github.com/sarbanha))
- Improves the performance of operations on tags (thanks to [@theriverman](https://github.com/theriverman))
- Remove `write` permission from Trello importer (thanks to [@northben](https://github.com/northben))
- DOCKER: Use python-3.11-slim as base image
- DOCKER: Adapt Dockerfile to the removal of psycopg2-binary
- DOCKER: Added env `POSTGRES_SSLMODE` with default value disabled (thanks to [@ribeiromiranda](https://github.com/ribeiromiranda))

## 6.5.2 (2022-09-26)

- Updated links to the Taiga community site.
- Update locales.
- Drop psycopg2-binary dependency; use psycopg2 instead

## 6.5.1 (2022-01-27)

- The maximum number of pending invitations is per project again.
- Add more stats in the User detail section in the admin panel.

## 6.5.0 (2022-01-24)

- Now member limits by projects are counted by owner and not by project
- Fix Trello importer, now it does not generate empty attachments (issue #tg-4782)
- Fix previsualization of .psd files for attachments, project logos and user avatars
- Upgrade project dependencies. Now taiga only works with python >= 3.7

## 6.4.3 (2021-10-27)

- Update locales

## 6.4.2 (2021-09-16)

- Update locales

## 6.4.1 (2021-09-08)

- fix(settings): increase default lifetime of ACCESS and REFRESH token
- fix(userstories): invalid serializer for userstories if only_ref=true

## 6.4.0 (2021-09-06)

- Serve Taiga in subpath
- Add new serializer to userstories endpoint witn minimal info (id, ref) (issue #tg-4739)

## 6.3.0 (2021-08-10)

- New Auth module, based on djangorestframework-simplejwt (history #tg-4625, issue #tgg-626))
- Fix the user when closing an issue from Github (issue #tg-4563)

## 6.2.2 (2021-07-15)

- Add date_cancelled to User
- Avoid logging in the history changes in the attachment's urls or its order (issue #tg-4247)
- Username and email are case insensitive for new registrations.

## 6.2.1 (2021-06-22)

- Add new bulk_order_update endpoint to reorder attachments in bulk (issue #tgg-218)
- [Performance] User stories endpoint is too slow for dashboard queries (issue #tg-4600)

## 6.2.0 (2021-06-09)

- Change api response from 404 to 401 when not logged in (issues #tg-4415, #tg-4301)
- Allows to order issues by 'ref' field (issue #tg-4503)
- Generate history entries, timeline entries and webhook requests after kanban order is updated (issues #tg-4311, #tg-4340)
- Fix showing epic-related private uss on a public timeline (issue #tg-4291)
- Fix filter userstories by assignation for registered no-member users (issue #tg-2533)
- New algorithm to reorder user stories in the backlog (issue #tg-62)
- Fix wrong behaviour, deleted (inactive) users can still perform API calls (issue #tg-732)

## 6.1.1 (2021-05-18)

- Fix user avatar in Trello importer

## 6.1.0 (2021-05-04)

- Render markdown to html for checkbox
- Update github templates

## 6.0.9 (2021-04-13)

- Migrated to weblate and new translations
- Update dependencies

## 6.0.8 (2021-04-13)

- Improve docker configuration
- fix(userstories): close or open userstories afte they are moved in bulk in kanban

## 6.0.7 (2021-03-09)

- fix(email): catch smtp errors to prevent app crashes

## 6.0.6 (2021-03-01)

- Fix api message

## 6.0.5 (2021-02-22)

- Added translation to Dansk
- Added translation to Serbian
- Added translation to Vietnamese
- Simplify and improve docker configuration
- Improve Github integration (edit, close and reopen issue events)
- Fix Asana importer

## 6.0.4 (2021-02-15)

### Misc

- Fix importer: ignore epic related user stories from another project
- Change default sitemap page size
- Improve docker configuration

## 6.0.3 (2020-02-08)

### Misc

- Fix: ENABLE_WEBHOOKS for docker images

## 6.0.2 (2020-02-08)

### Features

- Update colors for default project template fixtures.

### Misc

- Minor fixes related to importers and integrations.

## 6.0.1 (2020-02-02)

### Misc

- Fix 'create user' form in django admin panel.

## 6.0.0 (2020-02-02)

### Features

- Swimlanes
- Generate docker image
- Revamp email design
- Improve Gitlab integration (edit, close and reopen issue events)

### Misc

- Changed the configuration style to expect DJANGO_SETTINGS_MODULE
- Improved performance when reordering
- Updated dependencies

## 5.5.9 (2020-12-21)

### Fix

- Fix attachment refresh feature.
- Fix welcome email template layout.

### Misc

- Updated requirements. **Please note that Python 3.5 is not supported**.
- Several minor changes.

### i18n

- Add Arabic.
- Update Russian.

## 5.5.7 (2020-11-11)

### Misc

- Upgrade requirements.
- Fix deprecation warnings.

## 5.5.5 (2020-09-16)

### Misc

- Improve verify email feature for invited users.

### i18n

- Update catalog.
- Update fa.

## 5.5.4 (2020-09-08)

### Misc

- Upgrade requirements.

### i18n

- Update French translation.

## 5.5.3 (2020-09-02)

### Misc

- Parametrize mdrender cache options.
- Minor bug fix.

## 5.5.2 (2020-08-26)

### Misc

- Tweaks mdrender cache.

## 5.5.1 (2020-08-23)

### Features

- Prevent member creation to users with unverified email address.

## 5.5.0 (2020-08-19)

### Features

- Verify user email.
- Task promotion creates user story and deletes original task.

### Misc

- Upgraded Django version to 2.2. This is a BREAKING CHANGE. Contributed
  modules should be upgraded.
- Several minor bugfixes.

## 5.0.15 (2020-06-17)

### Misc

- Fixed bug old dump format project import.

## 5.0.14 (2020-06-16)

### Misc

- Fixed several minor bugs.

## 5.0.13 (2020-06-08)

### Features

- Resolved Django deprecation warnings to prepare for an upgrade.
- Added option to disallow anonymous access to user profiles.

### Misc

- Updated requirements.
- Use pip-tools to manage dependencies.

### i18n

- Updated translations (lv).

## 5.0.12 (2020-05-12)

### Security

- Avoid change in membership attribute. We encourage all users of Taiga
  to upgrade as soon as possible.

## 5.0.11 (2020-05-04)

### Misc

- Fixed several minor bugs.
- Updated requirements.

### i18n

- Updated translations (es, lv, ru, tr, uk).

## 5.0.9 (2020-03-11)

### Feature

- Implemented new simplified email messages.

### Misc

- Fixed several minor bugs.
- Updated requirements.

### i18n

- Updated lots of strings and updated their translations.

## 5.0.8 (2020-02-17)

### i18n

- Update Basque translation and others.

### Misc

- Several minor bugfixes.

## 5.0.7 (2020-02-06)

### Feature

- Add reduce notifications configuration option.
- Sanitize full name input.

### i18n

- Add Latvian translation.

### Misc

- Several minor bugfixes.

## 5.0.6 (2020-01-15)

### Misc

- Minor fix on contact project team feature.

## 5.0.5 (2020-01-08)

### Feature

- Promote task and issues to user story with watchers, attachments and comments.

### Misc

- Several minor bugfixes and translation updates.

## 5.0.0 (2019-11-13)

- Refresh attachment URL on markdown fields to support protected backend.
- Update requirements.
- Update translations: Persian (Iran), French, Portuguese (Brazil).

## 4.2.14 (2019-10-01)

- Update requirements to support python3.7. This is a potentially BREAKING
  CHANGE. Several libraries were updated to minor and patch releases.
  Contributed modules should be tested thoroughly.
- Minor bug fixes.

## 4.2.12 (2019-08-06)

### Misc

- Upgrade requirements
- Events refactoring

## 4.2.11 (2019-07-24)

### Misc

- Asana bug fix.

## 4.2.10 (2019-07-11)

### Misc

- Remove role points project signal from patch US's.
- Improve US's statuses filter by project.


## 4.2.7 (2019-06-24)

### Misc

- Add default settings slug configuration.
- Minor bug fixes.

## 4.2.6 (2019-06-12)

### Misc

- Recreate timeline indexes.
- Minor bug fixes.


## 4.2.4 / 4.2.5 (2019-05-09)

### Misc

- Fix epics excluded filter (https://tree.taiga.io/project/taiga/issue/5727)
- Avoid saving non integer user id's in history diffs
- Upgrade requests dependence


## 4.2.3 (2019-04-16)

### Features:

- Change tag filter behavour to 'or' operator

### Misc

- Change milestone query
- Avoid getting non image thumbnails
- Remove unnecesary queries on saving items
- Update messages catalog
- Minor bug fixes.

## 4.2.2 (2019-03-21)

### Features:

- Fix milestone US serializer

## 4.2.1 (2019-03-20)

### Features:

- Add dashboard filter for user stories updating queryset and serializer
- Change milestone user story serializer
- Remove additional order by in timeline queryset
- Add user project slight queryset and serializer
- Filter history comments queryset

### Misc

- Minor bug fixes.

## 4.2.0 (2019-02-28)

### Features:

- Promote Tasks to US
- Improve queries
- Activate Hebrew and Basque languages

### Misc

- Minor bug fixes.

## 4.1.0 (2019-02-04)

### Misc

- Fix Close sprints

### Features:

- Negative filters
- Activate the Ukrainian language

## 4.0.4 (2019-01-15)

### Misc

- Minor bug fixes.

## 4.0.3 (2018-12-11)

### Misc

- Add extra requirements for oauthlib

## 4.0.2 (2018-12-04)

### Misc

- Update messages catalog.

## 4.0.1 (2018-11-28)

### Misc

- Minor bug fix.

## 4.0.0 Larix cajanderi (2018-11-28)

### Features

- Custom home section (https://tree.taiga.io/project/taiga/issue/3059)
- Custom fields (https://tree.taiga.io/project/taiga/issue/3725):
    - Dropdown
    - Checkbox
    - Number
- Bulk move unfinished objects in sprint (https://tree.taiga.io/project/taiga/issue/5451)
- Paginate history activity
- Improve notifications area (https://tree.taiga.io/project/taiga/issue/2165 and
  https://tree.taiga.io/project/taiga/issue/3752)

### Misc

- Minor icon changes
- Lots of small bugfixes

## 3.4.5 (2018-10-15)

### Features

- Prevent local Webhooks

## 3.4.4 (2018-09-19)

### Misc

- Small fixes

## 3.4.3 (2018-09-19)

### Misc

- Refactor attachment url's in timeline
- Avoid receive feedkback in private projects from non-members
- Allow delete reports uuid's
- Small fixes

## 3.4.0 Pinus contorta (2018-08-13)

### Features

- Due dates configuration (https://tree.taiga.io/project/taiga/issue/3070):
    - Add due dates to admin attributes
    - Update project templates
- Issues to Sprints (https://tree.taiga.io/project/taiga/issue/1181):
    - Add milestone filters

## 3.3.14 (2018-08-06)

### Misc

- Improve US reorder algorithm.
- Drop python 3.4 and add python 3.6 to travis configuration.

## 3.3.13 (2018-07-05)

### Misc

- Minor bug fixes.

## 3.3.11 (2018-06-27)

### Features

- Add assigned users kanban/taskboard filter.
- Improve US reorder in kanban.
- Upgrade psycopg2 library.

## 3.3.8 (2018-06-14)

### Misc

- Minor bug fix.

## 3.3.7 (2018-05-31)

### Misc

- Minor bug fix related with project import.
- Pin requirements to solve incompatible versions detected by pip 10.

## 3.3.4 (2018-05-24)

### Misc

- Add features to fulfill GDPR.

## 3.3.3 (2018-05-10)

### Misc

- Update locales.
- Minor bug fixes.

## 3.3.1 (2018-04-30)

### Misc

- Minor bug fixes.

## 3.3.1 (2018-04-30)

### Misc

- Minor bug fixes.

## 3.3.0 Picea mariana (2018-04-26)

### Features

- Add "live notifications" to Taiga:
    - Migration for user configuration.
- Add due date to US, tasks and issues (https://tree.taiga.io/project/taiga/issue/3070):
    - Add to csv export.
    - Add to projects import/export.
    - Add to webhooks.
    - Add to django admin.
- Add multiple assignement only in US (https://tree.taiga.io/project/taiga/issue/1961):
    - The `assigned_to` field is still active.
    - Add to csv export.
    - Add to projects import/export.
    - Add to webhooks.
    - Add to django admin.
- Delete cards in Kanban and sprint Taskboard (https://tree.taiga.io/project/taiga/issue/2683).

## 3.2.3 (2018-04-04)

### Misc

- Fix milestone burndown graph with empty US.
- Upgrade markdown library to solve bug.
- Update locales.

## 3.2.2 (2018-03-15)

### Misc

- Minor bug fixes.


## 3.2.0 Betula nana (2018-03-07)

### Features
- Add role filtering in US.


## 3.1.3 (2018-02-28)

### Features
- Increase token entropy.
- Squash field changes on notification emails
- Minor bug fixes.


## 3.1.0 Perovskia Atriplicifolia (2017-03-10)

### Features
- Contact with the project: if the projects have this module enabled Taiga users can contact them.
- Ability to create rich text custom fields in Epics, User Stories, Tasks and Isues.
- Full text search now use simple as tokenizer so search with non-english text are allowed.
- Duplicate project: allows creating a new project based on the structure of another (status, tags, colors, default values...)
- Add thumbnails and preview for PSD files.
- Add thumbnails and preview for SVG files (Cario lib is needed).
- i18n:
  - Add japanese (ja) translation.
  - Add korean (ko) translation.
  - Add chinese simplified (zh-Hans) translation.
- Third party services project importers:
  - Trello
  - Jira 7
  - Github
  - Asana

### Misc
- API:
    - Memberships API endpoints now allows using usernames and emails instead of using only emails.
    - Contacts API allow full text search (by the username, full name or email).
    - Filter milestones, user stories and tasks by estimated_start and estimated_finish dates.
    - Add project_extra_info to epics, tasks, milestones, issues and wiki pages endpoints.
- Gogs integration: Adding new Gogs signature method.
- Lots of small and not so small bugfixes.


## 3.0.0 Stellaria Borealis (2016-10-02)

### Features
- Add Epics.
- Include created, modified and finished dates for tasks in CSV reports.
- Add gravatar url to Users API endpoint.
- ProjectTemplates now are sorted by the attribute 'order'.
- Create enpty wiki pages (if not exist) when a new link is created.
- Diff messages in history entries now show only the relevant changes (with some context).
- User stories and tasks listing API call support extra params to include more data (tasks and attachemnts and attachments, respectively)
- Comments:
    - Now comment owners and project admins can edit existing comments with the history Entry endpoint.
    - Add a new permissions to allow add comments instead of use the existent modify permission for this purpose.
- Tags:
    - New API endpoints over projects to create, rename, edit, delete and mix tags.
    - Tag color assignation is not automatic.
    - Select a color (or not) to a tag when add it to stories, issues and tasks.
- Improve search system over stories, tasks and issues:
    - Search into tags too. (thanks to [Riccardo Cocciol](https://github.com/volans-))
    - Weights are applied: (subject = ref > tags > description).
- Import/Export:
    - Gzip export/import support.
    - Export performance improvements.
- Add filter by email domain registration and invitation by setting.
- Third party integrations:
    - Included gogs as builtin integration.
    - Improve messages generated on webhooks input.
    - Add mentions support in commit messages.
    - Cleanup hooks code.
    - Rework webhook signature header to align with larger implementations and defined [standards](https://superfeedr-misc.s3.amazonaws.com/pubsubhubbub-core-0.4.html\#authednotify). (thanks to [Stefan Auditor](https://github.com/sanduhrs))
- Add created-, modified-, finished- and finish_date queryset filters
    - Support exact match, gt, gte, lt, lte
    - added issues, tasks and userstories accordingly
- i18n:
  - Add norwegian Bokmal (nb) translation.

### Misc
- [API] Improve performance of some calls over list.
- Lots of small and not so small bugfixes.


## 2.1.0 Ursus Americanus (2016-05-03)

### Features
- Add sprint name and slug on search results for user stories (thanks to [@everblut](https://github.com/everblut))
- [API] projects resource: Random order if `discover_mode=true` and `is_featured=true`.
- Webhooks: Improve webhook data:
    - add permalinks
    - owner, assigned_to, status, type, priority, severity, user_story, milestone, project are objects
    - add role to 'points' object
    - add the owner to every notification ('by' field)
    - add the date of the notification ('date' field)
    - show human diffs in 'changes'
    - remove unnecessary data
- CSV Reports:
    - Change field name: 'milestone' to 'sprint'
    - Add new fields: 'sprint_estimated_start' and 'sprint_estimated_end'
- Importer:
    - Remove project after load a dump file fails
    - Add more info the the logger if load a dump file fails

### Misc
- Lots of small and not so small bugfixes.


## 2.0.0 Pulsatilla Patens (2016-04-04)

### Features
- Ability to create url custom fields. (thanks to [@astagi](https://github.com/astagi)).
- Blocked projects support
- Transfer projects ownership support
- Customizable max private and public projects per user
- Customizable max of memberships per owned private and public projects

### Misc
- Lots of small and not so small bugfixes.


## 1.10.0 Dryas Octopetala (2016-01-30)

### Features
- Add logo field to project model
- Add is_featured field to project model
- Add is_looking_for_people and looking_for_people_note fields to project model
- Filter projects list by
    - is_looking_for_people
    - is_featured
    - is_backlog_activated
    - is_kanban_activated
- Search projects by text query (order by ranking name > tags > description)
- Order projects list:
    - alphabetically by default
    - by fans (last week/moth/year/all time)
    - by activity (last week/moth/year/all time)
- Show stats for discover secction
- i18n.
  - Add swedish (sv) translation.
  - Add turkish (tr) translation.

### Misc
- Lots of small and not so small bugfixes.


## 1.9.1 Taiga Tribe (2016-01-05)

### Features
- [CSV Reports] Add fields "created_date", "modified_date", "finished_date" to issues CSV report.
- [Attachment] Generate 'card-image' size (300x200) thumbnails for attached image files.

### Misc
- Improve login and forgot password: allow username or email case-insensitive if the query only
  match with one user.
- Improve the django admin panel, now it is more usable and all the selector fields works properly.
- [API] Add tribe_gig field to user stories (improve integration between Taiga and Taiga Tribe).
- [API] Performance improvements for project stats.
- [Events] Add command to send an instant notifications to all the currently online users.
- Lots of small and not so small bugfixes.


## 1.9.0 Abies Siberica (2015-11-02)

### Features
- Project can be starred or unstarred and the fans list can be obtained.
- US, tasks and Issues can be upvoted or downvoted and the voters list can be obtained.
- Now users can watch public issues, tasks and user stories.
- Add endpoints to show the watchers list for issues, tasks and user stories.
- Add a "field type" property for custom fields: 'text', 'multiline text' and 'date' right nowi
  (thanks to [@artlepool](https://github.com/artlepool)).
- Allow multiple actions in the commit messages.
- Now every user that coments USs, Issues or Tasks will be involved in it (add author to the watchers list).
- Now profile timelines only show content about the objects (US/Tasks/Issues/Wiki pages) you are involved.
- Add custom videoconference system.
- Fix the compatibility with BitBucket webhooks and add issues and issues comments integration.
- Add support for comments in the Gitlab webhooks integration.
- Add externall apps: now Taiga can integrate with hundreds of applications and service.
- Improve searching system, now full text searchs are supported
- Add sha1 hash to attachments to verify the integrity of files (thanks to [@astagi](https://github.com/astagi)).
- i18n.
  - Add italian (it) translation.
  - Add polish (pl) translation.
  - Add portuguese (Brazil) (pt_BR) translation.
  - Add russian (ru) translation.

### Misc
- Made compatible with python 3.5.
- Migrated to django 1.8.
- Update the rest of requirements to the last version.
- Improve export system, now is more efficient and  prevents possible crashes with heavy projects.
- API: Mixin fields 'users', 'members' and 'memberships' in ProjectDetailSerializer.
- API: Add stats/system resource with global server stats (total project, total users....)
- API: Improve and fix some errors in issues/filters_data and userstories/filters_data.
- API: resolver suport ref GET param and return a story, task or issue.
- Webhooks: Add deleted datetime to webhooks responses when isues, tasks or USs are deleted.
- Add headers to allow threading for notification emails about changes to issues, tasks, user stories,
  and wiki pages. (thanks to [@brett](https://github.com/brettp)).
- Lots of small and not so small bugfixes.


## 1.8.0 Saracenia Purpurea (2015-06-18)

### Features
- Improve timeline resource.
- Add sitemap of taiga-front (the web client).
- Search by reference (thanks to [@artlepool](https://github.com/artlepool))
- Add call 'by_username' to the API resource User
- i18n.
  - Add deutsch (de) translation.
  - Add nederlands (nl) translation.

### Misc
- Lots of small and not so small bugfixes.


## 1.7.0 Empetrum Nigrum (2015-05-21)

### Features
- Make Taiga translatable (i18n support).
- i18n.
  - Add spanish (es) translation.
  - Add french (fr) translation.
  - Add finish (fi) translation.
  - Add catalan (ca) translation.
  - Add traditional chinese (zh-Hant) translation.
- Add Jitsi to our supported videoconference apps list
- Add tags field to CSV reports.
- Improve history (and email) comments created by all the GitHub actions

### Misc
- New contrib plugin for letschat (by Δndrea Stagi)
- Remove djangorestframework from requirements. Move useful code to core.
- Lots of small and not so small bugfixes.


## 1.6.0 Abies Bifolia (2015-03-17)

### Features
- Added custom fields per project for user stories, tasks and issues.
- Support of export to CSV user stories, tasks and issues.
- Allow public projects.

### Misc
- New contrib plugin for HipChat (by Δndrea Stagi).
- Lots of small and not so small bugfixes.
- Updated some requirements.


## 1.5.0 Betula Pendula - FOSDEM 2015 (2015-01-29)

### Features
- Improving SQL queries and performance.
- Now you can export and import projects between Taiga instances.
- Email redesign.
- Support for archived status (not shown by default in Kanban).
- Removing files from filesystem when deleting attachments.
- Support for contrib plugins (existing yet: slack, hall and gogs).
- Webhooks added (crazy integrations are welcome).

### Misc
- Lots of small and not so small bugfixes.


## 1.4.0 Abies veitchii (2014-12-10)

### Features
- Bitbucket integration:
  + Change status of user stories, tasks and issues with the commit messages.
- Gitlab integration:
  + Change status of user stories, tasks and issues with the commit messages.
  + Sync issues creation in Taiga from Gitlab.
- Support throttling.
  + for anonymous users
  + for authenticated users
  + in import mode
- Add project members stats endpoint.
- Support of leave project.
- Control of leave a project without admin user.
- Improving OCC (Optimistic concurrency control)
- Improving some SQL queries using djrom directly

### Misc
- Lots of small and not so small bugfixes.


## 1.3.0 Dryas hookeriana (2014-11-18)

### Features
- GitHub integration (Phase I):
  + Login/singin connector.
  + Change status of user stories, tasks and issues with the commit messages.
  + Sync issues creation in Taiga from GitHub.
  + Sync comments in Taiga from GitHub issues.

### Misc
- Lots of small and not so small bugfixes.


## 1.2.0 Picea obovata (2014-11-04)

### Features
- Send an email to the user on signup.
- Emit django signal on user signout.
- Support for custom text when inviting users.

### Misc
- Lots of small and not so small bugfixes.


## 1.1.0 Alnus maximowiczii (2014-10-13)

### Misc
- Fix bugs related to unicode chars on attachments.
- Fix wrong static url resolve usage on emails.
- Fix some bugs on import/export api related with attachments.


## 1.0.0 (2014-10-07)

### Misc
- Lots of small and not so small bugfixes

### Features
- New data exposed in the API for taskboard and backlog summaries
- Allow feedback for users from the platform
- Real time changes for backlog, taskboard, kanban and issues
