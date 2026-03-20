# dataset/README.md — FlexTrack Demo Data

This folder contains all seed/demo data for the FlexTrack Gym Management System.
**Edit these files to change demo data. No Python code changes required.**

To re-seed the database after editing:
```bash
# Default (upsert — safe to run multiple times)
.venv\Scripts\python.exe -m model.seed

# Full reset (drops all tables first, then re-seeds from scratch)
.venv\Scripts\python.exe -m model.seed --reset
```

---

## Files

### `users.json`
App login accounts (admin + staff).

| Field      | Type   | Notes                          |
|------------|--------|--------------------------------|
| `id`       | int    | Stable ID (used for upsert)    |
| `username` | string | Unique login name              |
| `email`    | string | Unique email                   |
| `password` | string | Plain text — hashed on seed    |
| `role`     | string | `"admin"` or `"staff"`         |

---

### `members.json`
Gym member registrations.

| Field       | Type   | Notes                               |
|-------------|--------|-------------------------------------|
| `id`        | int    | Stable ID                           |
| `full_name` | string |                                     |
| `phone`     | string |                                     |
| `email`     | string | Unique                              |
| `dob`       | string | ISO date `"YYYY-MM-DD"`             |
| `gender`    | string | `"male"`, `"female"`, `"other"`     |
| `join_date` | string | ISO date `"YYYY-MM-DD"`             |
| `status`    | string | `"active"` or `"inactive"`          |

---

### `packages.json`
Membership package definitions.

| Field            | Type   | Notes                          |
|------------------|--------|--------------------------------|
| `id`             | int    | Stable ID                      |
| `name`           | string |                                |
| `duration_unit`  | string | `"months"` or `"days"`         |
| `duration_value` | int    | Number of units                |
| `price`          | float  |                                |
| `description`    | string |                                |

---

### `trainers.json`
Personal trainer roster.

| Field                   | Type   | Notes |
|-------------------------|--------|-------|
| `id`                    | int    |       |
| `full_name`             | string |       |
| `phone`                 | string |       |
| `specialty`             | string |       |
| `availability_schedule` | string |       |

---

### `subscriptions.json`
Member-to-package links.

| Field        | Type   | Notes                                  |
|--------------|--------|----------------------------------------|
| `id`         | int    | Stable ID                              |
| `member_id`  | int    | Must match `members.json` `id`         |
| `package_id` | int    | Must match `packages.json` `id`        |
| `start_date` | string | `"YYYY-MM-DD"`                         |
| `end_date`   | string | `"YYYY-MM-DD"`                         |
| `status`     | string | `"active"`, `"expired"`, `"cancelled"` |

---

### `checkins.json`
Member gym check-in records.

| Field       | Type   | Notes                          |
|-------------|--------|--------------------------------|
| `id`        | int    |                                |
| `member_id` | int    | Must match `members.json` `id` |
| `timestamp` | string | `"YYYY-MM-DDTHH:MM:SS"`        |

---

### `payments.json`
Payment transactions.

| Field             | Type   | Notes                                        |
|-------------------|--------|----------------------------------------------|
| `id`              | int    |                                              |
| `member_id`       | int    | Must match `members.json` `id`               |
| `subscription_id` | int    | Must match `subscriptions.json` `id`         |
| `amount`          | float  |                                              |
| `method`          | string | `"cash"`, `"card"`, `"bank"`                 |
| `date`            | string | `"YYYY-MM-DD"`                               |
| `note`            | string |                                              |

---

### `plans.json`
Training plans linking members ↔ trainers.

| Field             | Type   | Notes                              |
|-------------------|--------|------------------------------------|
| `id`              | int    |                                    |
| `member_id`       | int    | Must match `members.json` `id`     |
| `trainer_id`      | int    | Must match `trainers.json` `id`    |
| `goal`            | string |                                    |
| `weekly_schedule` | object | JSON object `{"Mon": "...", ...}`  |
| `notes`           | string |                                    |
