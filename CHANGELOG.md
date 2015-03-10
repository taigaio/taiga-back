# Changelog #


## 1.6.0 ??? (Unreleased)

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
