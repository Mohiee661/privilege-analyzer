# Data Dictionary

This repository is file-based. All source datasets live in `data/` and are loaded by `services/data_loader.py`.

## Common Conventions

- `email` values are the primary join key across datasets.
- `platform` values are stored as human-readable names in the source JSON and normalized in code to keys such as `ad`, `azure`, `aws`, `okta`, and `salesforce`.
- `risk_context` is a documented exception or justification on a specific platform account. A non-null value should be treated as context, not automatically as a false positive.

## `data/ad_users.json`

Platform: Active Directory

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `user_id` | string | Unique account identifier in the synthetic AD dataset | `USR003` | Active Directory |
| `name` | string | Human-readable display name | `Amelia Johnson` | Active Directory |
| `email` | string | Primary email used for correlation | `amelia.johnson@company.com` | Active Directory |
| `department` | string | Organizational department | `Sales` | Active Directory |
| `status` | string | Account state such as active, disabled, or suspended | `active` | Active Directory |
| `platform` | string | Source platform label | `Active Directory` | Active Directory |
| `role` | string | Stated role on the platform | `Contractor` | Active Directory |
| `last_login` | string | ISO timestamp of the last observed login | `2026-05-21T21:00:00` | Active Directory |
| `account_type` | string | Account classification, usually `human` or service-style account | `human` | Active Directory |
| `owner_email` | string | Responsible owner or delegate contact | `lucas.lewis@company.com` | Active Directory |
| `mfa_enabled` | boolean | Whether MFA is enabled | `true` | Active Directory |
| `risk_context` | string or null | Documented exception or justification | `approved_role_transition:HR-TICKET-5102` | Active Directory |

## `data/azure_users.json`

Platform: Azure AD

Same schema and meaning as `ad_users.json`, but `platform` is `Azure AD`.

## `data/aws_users.json`

Platform: AWS IAM

Same schema and meaning as `ad_users.json`, but `platform` is `AWS IAM`.

## `data/okta_users.json`

Platform: Okta

Same schema and meaning as `ad_users.json`, but `platform` is `Okta`.

## `data/salesforce_users.json`

Platform: Salesforce

Same schema and meaning as `ad_users.json`, but `platform` is `Salesforce`.

## `data/login_events.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `event_id` | string | Unique login event identifier | `EVT001` | All platforms that emit login telemetry |
| `email` | string | Identity email associated with the event | `liam.jackson@company.com` | All platforms |
| `platform` | string | Source platform of the event | `Active Directory` | All platforms |
| `timestamp` | string | ISO timestamp of the event | `2026-06-17T09:00:00` | All platforms |
| `event_type` | string | Event category, usually `login` | `login` | All platforms |

## `data/offboarding_records.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `record_id` | string | Unique offboarding record identifier | `OFF001` | Identity lifecycle / HR |
| `email` | string | Identity email tied to the offboarding event | `amelia.johnson@company.com` | All identities |
| `termination_date` | string | ISO date of termination or offboarding action | `2025-12-02` | Identity lifecycle / HR |
| `reason` | string | Reason text for the offboarding event | `Role Reassignment` | Identity lifecycle / HR |

## `data/group_memberships.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `group_id` | string | Unique group identifier | `GRP001` | Platform group graph |
| `platform` | string | Platform that owns the group | `Active Directory` | Platform group graph |
| `group_name` | string | Friendly group name | `ad-global-admins` | Platform group graph |
| `grants_role` | string | Role inherited from membership in this group | `Administrator` | Platform group graph |
| `parent_group_id` | string or null | Parent group for nested group traversal | `GRP010` | Platform group graph |
| `direct_members` | array of strings | Emails directly assigned to the group | `[]` | Platform group graph |

## `data/privilege_events.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `event_id` | string | Unique privilege-change event identifier | `PEV001` | All platforms with role-change telemetry |
| `email` | string | Identity email associated with the change | `noah.kumar@company.com` | All platforms |
| `platform` | string | Source platform of the event | `Azure AD` | All platforms |
| `event_type` | string | Type of privilege change | `role_granted` | All platforms |
| `old_value` | string | Previous role or entitlement | `Employee` | All platforms |
| `new_value` | string | New role or entitlement | `Developer` | All platforms |
| `timestamp` | string | ISO timestamp of the event | `2026-06-18T18:00:00` | All platforms |
| `approved_by` | string or null | Approver identity if the change was approved | `None` | All platforms |

## `data/api_tokens.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `token_id` | string | Unique API token identifier | `TOK001` | Platform API credentials |
| `owner_email` | string | Email of the token owner | `svc-backup-job-09@company.com` | Platform API credentials |
| `platform` | string | Platform the token belongs to | `AWS IAM` | Platform API credentials |
| `scope` | string | Declared token scope | `read-only` | Platform API credentials |
| `created_date` | string | ISO date the token was created | `2025-03-07` | Platform API credentials |
| `last_rotated` | string | ISO date the token was last rotated | `2026-05-16` | Platform API credentials |
| `last_used` | string | ISO timestamp for last observed use | `2026-06-09T18:00:00` | Platform API credentials |
| `observed_write_call` | boolean | Whether a write action was observed | `false` | Platform API credentials |
| `status` | string | Credential status such as active or expired | `active` | Platform API credentials |

## `data/ground_truth_labels.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `email` | string | Identity email used to join against risk profiles | `amelia.johnson@company.com` | All identities |
| `category` | string | Ground-truth class label for the identity | `offboarding_gap` | Evaluation dataset |
| `is_anomalous` | boolean | Whether the record should be considered risky | `true` | Evaluation dataset |
| `is_false_positive_trap` | boolean | Whether the record was intentionally designed as a safe exception / trap | `false` | Evaluation dataset |

## `data/demo_scenarios.json`

| Field | Type | Meaning | Example | Applies to |
| --- | --- | --- | --- | --- |
| `scenario_id` | string | Stable demo scenario identifier | `SCN001` | Demo UI |
| `title` | string | Short scenario title | `Ghost Employee` | Demo UI |
| `person_id` | string | Synthetic person identifier | `DEMO001` | Demo UI |
| `name` | string | Display name for the demo identity | `Evan Carter` | Demo UI |
| `email` | string | Identity email for the demo card | `evan.carter@company.com` | Demo UI |
| `risk_score` | number | Precomputed demo risk score | `97` | Demo UI |
| `risk_level` | string | Precomputed risk bucket | `CRITICAL` | Demo UI |
| `finding_type` | string | Primary risk type shown in the demo | `OFFBOARDING_GAP` | Demo UI |
| `summary` | string | Human-readable explanation for the demo card | `AD is disabled while AWS and Okta remain active.` | Demo UI |
| `accounts` | object | Nested per-platform account snapshot | `{ "ad": { "status": "disabled", "role": "Employee" } }` | Demo UI |
| `timeline` | array of objects | Chronological event list for the scenario | `[{ "date": "2026-03-01", "event": "AD account disabled" }]` | Demo UI |

## Synthetic Category Design

The ground-truth dataset contains one baseline class and nine synthetic anomaly categories.

| Category | Approx. share | Notes |
| --- | --- | --- |
| `normal` | 33.5% | Baseline identities without a labeled anomaly |
| `legitimate_trap` | 13.9% | Intentional safe exception used to test false-positive suppression |
| `multi_platform_admin` | 11.3% | Same identity has admin access across multiple platforms |
| `offboarding_gap` | 8.3% | Disabled in one system but still active elsewhere |
| `nested_group_hidden_admin` | 7.4% | Admin privilege inherited through nested group membership |
| `dormant_admin` | 7.0% | Privileged account that has gone unused for a long period |
| `privilege_escalation` | 6.1% | Unapproved or suspicious privilege change sequence |
| `suspended_mismatch` | 5.7% | Suspended in one place but active in another |
| `orphaned_service_account` | 3.9% | Service identity without an obvious owner or lifecycle control |
| `token_abuse` | 3.0% | API token misuse, stale tokens, or write activity beyond scope |

These percentages are based on the current `data/ground_truth_labels.json` distribution and may shift if the dataset is regenerated.

