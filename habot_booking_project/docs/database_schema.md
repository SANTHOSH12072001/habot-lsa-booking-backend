# Database Schema

## Parent

| Column | Type | Constraint |
|---|---|---|
| id | UUID | Primary key |
| full_name | VARCHAR(120) | Required |
| email | VARCHAR | Unique, indexed |
| phone | VARCHAR(30) | Optional |
| created_at | TIMESTAMP | Required |

## LSAProfile

| Column | Type | Constraint |
|---|---|---|
| id | UUID | Primary key |
| full_name | VARCHAR(120) | Required |
| email | VARCHAR | Unique, indexed |
| bio | TEXT | Optional |
| hourly_rate | DECIMAL(10,2) | >= 0 |
| is_active | BOOLEAN | Indexed |
| skills | JSON | List of skills |
| created_at | TIMESTAMP | Required |

## BookingRequest

| Column | Type | Constraint |
|---|---|---|
| id | UUID | Primary key |
| parent_id | UUID | Foreign key |
| lsa_id | UUID | Foreign key |
| session_start | TIMESTAMP | Indexed |
| session_end | TIMESTAMP | Indexed |
| status | VARCHAR(30) | Indexed |
| amount | DECIMAL(10,2) | >= 0 |
| external_reference | VARCHAR(120) | Indexed |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

Indexes:
- `(lsa, session_start, session_end)`
- `(parent, session_start)`
- `(status, session_start)`

## Payment

| Column | Type | Constraint |
|---|---|---|
| id | UUID | Primary key |
| booking_id | UUID | Unique foreign key |
| provider | VARCHAR(50) | Required |
| transaction_id | VARCHAR(120) | Unique |
| status | VARCHAR(20) | Indexed |
| amount | DECIMAL(10,2) | >= 0 |
| raw_payload | JSON | Optional |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |
