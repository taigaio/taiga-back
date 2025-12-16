# Refactoring Log

## Extract Method
- `_build_search_futures` extracted to assemble permissioned search submissions.  
  - Location: `taiga/searches/api.py` — `SearchViewSet._build_search_futures`
- `_collect_results` extracted to gather ThreadPoolExecutor results consistently.  
  - Location: `taiga/searches/api.py` — `SearchViewSet._collect_results`
- `_request_oauth_token` extracted to encapsulate Jira OAuth prompt/flow.  
  - Location: `taiga/importers/management/commands/import_from_jira.py` — `Command._request_oauth_token`

## Extract Class
- `SearchTaskExecutor` introduced to own search future orchestration and result collection.  
  - Location: `taiga/searches/api.py`
- `ImportStrategy` hierarchy introduced to encapsulate importer-specific behavior.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- `SearchPlanEntry` introduced to encapsulate permission + callable pairing for searches.  
  - Location: `taiga/searches/api.py`
- `UserBindingPrompter` introduced to encapsulate interactive user binding prompts.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`

## Rename Method/Variable
- Renamed request text to `query_text` for clarity on intent.  
  - Location: `taiga/searches/api.py` — `SearchViewSet.list`
- Renamed `_search_user_stories` to `_search_project_user_stories` to reflect scope.  
  - Location: `taiga/searches/api.py`
- Renamed `_search_tasks` to `_search_project_tasks` to mirror other search helpers.  
  - Location: `taiga/searches/api.py`

## Move Method/Field
- Moved search future orchestration/collection responsibilities into `SearchTaskExecutor`.  
  - Location: `taiga/searches/api.py`
- Pulled shared search result fields into `BaseSearchResultsSerializer`.  
  - Location: `taiga/searches/serializers.py`
- Moved issue-type binding logic into `ProjectImportStrategy._bind_issue_type`.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`

## Decompose Conditional
- Split token resolution into `_resolve_auth_token` with explicit anon/provided/OAuth branches.  
  - Location: `taiga/importers/management/commands/import_from_jira.py` — `Command._resolve_auth_token`
- Separated project type selection into `_choose_project_type`, removing mixed option/prompt logic.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- Decomposed importer choice into `_build_importer` instead of inline nested conditional.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`

## Replace Conditional with Polymorphism
- Replaced project/board conditional import handling with `ProjectImportStrategy` and `BoardImportStrategy`.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- Introduced `AuthTokenStrategy` variants (anon/provided/interactive) for token resolution.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- `SearchPlanEntry` governs permission checks vs inline conditionals.  
  - Location: `taiga/searches/api.py`

## Pull-up Variable/Method
- Shared search serializer fields pulled up into `BaseSearchResultsSerializer`.  
  - Location: `taiga/searches/serializers.py`
- Shared issue-type binding flow normalized via `_bind_issue_type` helper.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- Shared search plan construction captured in `SearchPlanEntry` usage.  
  - Location: `taiga/searches/api.py`

## Push-down Variable/Method
- Issue-type binding specialization pushed into `ProjectImportStrategy._bind_issue_type`.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- Board-specific import remains in `BoardImportStrategy.import_data`.  
  - Location: `taiga/importers/management/commands/import_from_jira.py`
- Epic/UserStory/Task/Issue serializers now inherit base but can extend with specialized fields (e.g., UserStory extras stay in subclass).  
  - Location: `taiga/searches/serializers.py`

## Introduce Explaining Variable
- Introduced `has_permission` flag when queueing searches to clarify guard condition.  
  - Location: `taiga/searches/api.py` — `SearchViewSet._build_search_futures`
- Introduced `token_option` to make token source explicit before branching.  
  - Location: `taiga/importers/management/commands/import_from_jira.py` — `Command.handle`
- Introduced `project_type_option` to separate option retrieval from selection logic.  
  - Location: `taiga/importers/management/commands/import_from_jira.py` — `Command.handle`

