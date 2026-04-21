# V2 Migration Status

## Purpose

This document tracks the current state of the quiz-data migration to V2, what has been completed, what is now operationally authoritative, and what migration-scoped work still remains before the legacy path can be considered fully deprecated and cleaned up.

This document is intentionally scoped to the database migration and cutover only. It does not cover unrelated application cleanup.

## Migration Objective

The migration introduced a normalized V2 data model so that quiz content, saved quiz references, quiz history, folders, and folder items can be managed through canonical V2 records rather than legacy duplicated payload storage.

The intended end state is:

- V2 collections are the authoritative store for supported quiz flows
- historical legacy data is backfilled into V2
- live reads and writes operate through V2
- legacy collections remain only for stabilization, rollback, audit, or archival until explicitly deprecated and removed

## V2 Collections

The migration currently centers on these collections:

- `quizzes_v2`
- `saved_quizzes_v2`
- `quiz_history_v2`
- `folders_v2`
- `folder_items_v2`

## Completed Stages

### Stage 1: V2 Foundation

Completed:

- V2 collections, validators, and indexes were introduced
- canonical quiz and reference models were added
- repository and write-service foundations were created

### Stage 2: Dual Writes

Completed:

- legacy write flows were mirrored into V2
- canonical/source mapping was introduced
- live traffic could populate V2 while legacy remained active

### Stage 3: Historical Backfill

Completed:

- historical legacy data was backfilled into V2
- reruns were hardened for idempotency
- stable fallback timestamps were introduced
- legacy saved/folder records without answer payloads were resolved safely against full legacy/V2 sources
- duplicate saved and folder-item convergence paths were hardened
- parity reporting and structured backfill summaries were added

Important note:

- environments that previously ran Stage 3 needed a rerun after later Stage 4 parity changes so `display_title` and folder-item `position` could be populated in V2

### Stage 4: Read Cutover

Completed:

- saved quiz, history, folder, and share reads were cut over to V2-backed read services
- read behavior was validated through compare-mode and then moved to `v2_only`
- response compatibility was preserved while the frontend transition was still underway
- folder ordering and user-facing title parity were aligned in V2

### Stage 5: Final V2 Cutover

Completed:

- V2 is now the default write path for migrated quiz-library flows
- V2 is the default read path for saved/history/folder/share flows
- generation/save/history/share flows now operate with canonical V2 quiz ids
- frontend authenticated library flows were updated to consume V2 ids and canonical quiz ids
- download-by-id was updated to resolve canonical V2 quizzes

## Current Operational State

Current config defaults:

- `QUIZ_V2_WRITE_MODE = "v2_only"`
- `QUIZ_V2_SAVED_READ_MODE = "v2_only"`
- `QUIZ_V2_HISTORY_READ_MODE = "v2_only"`
- `QUIZ_V2_FOLDER_READ_MODE = "v2_only"`
- `QUIZ_V2_SHARE_READ_MODE = "v2_only"`

Current authoritative behavior:

- saved quiz writes: V2
- history writes: V2
- folder writes: V2
- saved quiz reads: V2
- history reads: V2
- folder reads: V2
- shared quiz reads: V2
- generated quiz identity: canonical V2 id
- download by quiz id: supports canonical V2 quiz ids

## Migration Guarantees Achieved

The current implementation has achieved the main migration guarantees:

- historical data is migrated into V2
- key legacy edge cases discovered during migration are handled explicitly
- reruns are materially idempotent for supported backfill flows
- user-library data is served from V2
- supported library writes no longer require legacy persistence
- canonical quiz identity is now usable across core flows

## Remaining Migration-Scoped Work

The following items still remain if the goal is a fully completed migration and legacy deprecation process.

### 1. Remove or Retire Migration Compatibility Branches

The codebase still contains migration-era compatibility logic in some services, including:

- legacy-read branches
- compare-mode branches
- legacy-id compatibility shaping

These should be either:

- removed after the stabilization window, or
- explicitly retained as rollback-only logic with clear ownership and expiry

### 2. Finalize Public ID Contract

The migrated surfaces now expose V2 ids and canonical quiz ids, but some payloads still carry compatibility fields such as:

- `_id`
- `legacy_id`
- `legacy_quiz_id`

A final migration decision is still needed:

- which of these fields remain intentionally supported
- which are transitional and should be removed after stabilization

This is migration-scoped because it determines when legacy-id support truly ends.

### 3. Decide the Fate of Remaining Legacy-First Non-Core Routes

Some non-core or test-oriented legacy CRUD paths still exist in the codebase, especially around manual/test quiz routes.

Migration follow-up is needed to decide whether they should:

- be migrated to V2 as well
- be explicitly marked legacy/test-only
- be removed entirely

If they remain, they should not create ambiguity about whether legacy is still part of the normal production path.

### 4. Add Final Legacy-Usage Guardrails

After V2-only stabilization, the migration should add stronger guarantees that unsupported legacy access does not silently continue.

Examples:

- warning/error logs if deprecated legacy repositories are invoked
- assertions or tests for unsupported legacy write usage
- startup validation for invalid migration flag combinations

### 5. Complete Legacy Deprecation Plan

The migration is not fully complete until legacy collections have a defined post-cutover lifecycle.

A migration completion plan is still needed for:

- stabilization window length
- rollback expectations
- legacy collection archival policy
- final legacy collection removal plan

### 6. Optional Index Hardening After Stabilization

Code-level dedupe and merge protections are in place for several legacy-reference scenarios.

After production stabilization and duplicate cleanup are confirmed, the migration can consider stronger DB-level enforcement for legacy reference uniqueness where appropriate.

This should only happen after verifying there is no conflicting legacy residue in existing environments.

## What Is Not Considered a Migration Blocker

The following may still need work, but they are not by themselves evidence that the V2 migration failed:

- unrelated app cleanup
- generic refactors outside quiz-library migration surfaces
- existing deprecation warnings not introduced by the migration
- non-core UI polish issues

## Recommended Migration Close-Out Sequence

To finish the migration cleanly, the next migration-scoped sequence should be:

1. stabilize V2-only operation in target environments
2. monitor for unexpected legacy-path usage
3. decide which compatibility fields remain public and which are removed
4. retire compare/legacy branches that are no longer needed
5. document legacy archival/removal plan
6. execute final legacy deprecation/removal in a follow-up cleanup stage

## Summary

The migration has reached the point where V2 is operationally authoritative for the supported quiz-library flows. The remaining work is no longer about proving the V2 model; it is about finishing the deprecation and cleanup process so that legacy support becomes explicit, limited, and eventually removable.
