# Database Setup Instructions

## Initial Setup (One-time)

### Step 1: Create User and Database

Run the setup script as your PostgreSQL superuser to create the project's database and user:

```bash
psql postgres -f ./db/setup_db.sql
```

This script will:
- Create a database user: `benevity_user` with password: `alpine`
- Create a database: `benevity`
- Grant all necessary privileges to the user

### Step 2: Initialize Tables

After creating the database and user, initialize the tables using the new user:

```bash
psql -U benevity_user -d benevity -f ./db/init_db.sql
```

Or connect and run it manually:

```bash
psql -U benevity_user -d benevity
```

Then inside psql:
```sql
\i ./db/init_db.sql
```

## Verify Setup

Check that tables were created:

```bash
psql -U benevity_user -d benevity -c "\dt"
```

## Connection String

The application connects using this URI (already configured in `.env`):

```
postgresql://benevity_user:alpine@localhost:5432/benevity
```

## Troubleshooting

If you get a password prompt, PostgreSQL is configured to use password authentication. Enter: `alpine`

If you get "Peer authentication failed", you may need to update your `pg_hba.conf` to allow password authentication for the benevity_user.
