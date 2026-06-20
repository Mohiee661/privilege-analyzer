# Architecture

## System Overview

```text
                       +----------------------+
                       |   data/*.json files  |
                       |----------------------|
                       | platform users       |
                       | login events         |
                       | offboarding records  |
                       | group memberships    |
                       | privilege events     |
                       | api tokens           |
                       +----------+-----------+
                                  |
                                  v
                      +------------------------+
                      | correlation_engine.py  |
                      |------------------------|
                      | build unified identities
                      | by normalized email     |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      | risk_engine.py         |
                      |------------------------|
                      | rule-based detectors   |
                      | 8 finding types        |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      | scoring_engine.py      |
                      |------------------------|
                      | weighted risk scores   |
                      | risk_level buckets     |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      | ai_explainer.py        |
                      |------------------------|
                      | Groq narrative layer   |
                      | deterministic fallback |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      | output/*.json          |
                      | API + frontend consume  |
                      +------------------------+
```

This is a file-based pipeline. There is no database layer.

## Pipeline Flow

1. `services/correlation_engine.py`
   - Loads platform-specific user datasets from `data/*.json`.
   - Normalizes email addresses.
   - Groups records into unified identities.
   - Preserves each platform account in `output/unified_identities.json`.

2. `services/risk_engine.py`
   - Reads unified identities.
   - Applies deterministic rule-based detectors.
   - Emits `output/risk_findings.json`.

3. `services/scoring_engine.py`
   - Reads findings and unified identities.
   - Computes per-identity scores and risk levels.
   - Emits `output/risk_profiles.json`.

4. `services/ai_explainer.py`
   - Reads unified identities, findings, and risk profiles.
   - Calls Groq for narrative explanations when available.
   - Falls back to deterministic local text when Groq is unavailable.
   - Saves `output/ai_reports.json` and the cache file `output/ai_report_cache.json`.

## Detection Rules

All detections are deterministic and rule-based. The system does not use a trained ML classifier for finding generation.

### 1. `OFFBOARDING_GAP`
- Trigger: at least one account is `disabled` and at least one other account for the same identity is still `active`.
- Evidence: platform status map.
- Severity: `HIGH`.

### 2. `MULTI_PLATFORM_ADMIN`
- Trigger: the same identity has admin-equivalent roles on two or more platforms.
- Admin roles include values such as `Administrator`, `Global Administrator`, `Super Admin`, and similar variants listed in `services/risk_engine.py`.
- Severity: `HIGH`.

### 3. `STALE_ACTIVE_ACCOUNT`
- Trigger: an account is still `active` but its `last_login` is older than 180 days.
- Severity: `MEDIUM`.

### 4. `SUSPENDED_ACCOUNT_MISMATCH`
- Trigger: at least one platform shows `suspended` while another platform for the same identity remains `active`.
- Severity: `HIGH`.

### 5. `EXCESSIVE_PLATFORM_EXPOSURE`
- Trigger: the identity appears on four or more platforms.
- Severity: `MEDIUM`.

### 6. `HIDDEN_PRIVILEGE_VIA_GROUP_NESTING`
- Trigger: for a specific platform, the stated role is low privilege, but `effective_privilege(email, platform)` resolves to one or more admin-equivalent roles through nested group membership on that same platform.
- Severity: `HIGH`.

### 7. `UNAPPROVED_PRIVILEGE_SPIKE`
- Trigger: three or more privilege-changing events for the same email occur within a 7-day window and none of those events have `approved_by` set.
- Severity: `HIGH`.

### 8. `STALE_OR_MISUSED_TOKEN`
- Trigger: an API token is stale, meaning `last_rotated` is older than 365 days, or the token is scoped `read-only` but observed making a write call.
- Severity: `MEDIUM` for stale-only cases, `HIGH` when misuse is observed.

## Effective Privilege Graph Traversal

`services/privilege_graph.py` calculates inherited privilege using nested group memberships:

- It loads `group_memberships.json`.
- It normalizes platform names through aliases such as `Active Directory -> ad` and `Azure AD -> azure`.
- It builds two indexes:
  - `groups_by_id`: group ID to group record
  - `memberships_by_email`: direct member email to group IDs
- For a given email and platform, it filters memberships to that platform first.
- It then walks upward through `parent_group_id` recursively.
- At each group, it appends `grants_role` to the effective privilege list.
- Roles are deduplicated while preserving first-seen order.

This means effective privilege is the union of direct group grants plus any inherited parent-group grants on the same platform.

## AI / ML Approach

The AI layer is not a trained model used for detection.

What is rule-based:
- identity correlation
- risk detection
- scoring
- confidence inference from `risk_context`

What uses an LLM:
- `services/ai_explainer.py` sends the correlated identity, findings, score, and risk level to Groq for executive-friendly narrative generation.

Groq models:
- Preferred: `llama-3.3-70b-versatile`
- Fallback: `llama-3.1-8b-instant`

Behavior:
- If Groq succeeds, the report contains a concise summary, security impact, recommended actions, and confidence label.
- If Groq is unavailable, the system generates deterministic fallback text locally.
- If any platform account has a non-null `risk_context`, the report is treated as likely a documented exception and the confidence label becomes `likely_false_positive_pending_review`.
- Otherwise the report is treated as `likely_true_positive`.

This should be described as rule-based analytics plus LLM-assisted narrative generation, not as a trained ML detector.
