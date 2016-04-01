# Changelog #


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
