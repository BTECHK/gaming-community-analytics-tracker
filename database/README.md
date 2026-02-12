# gaming-community-analytics-tracker Database Management

Complete database backup, restore, and management scripts for PostgreSQL.

## Quick Start - Full Restore on Fresh Machine

```bash
# 1. Start PostgreSQL container
docker compose up -d db

# 2. Wait for db to be ready
docker compose exec db pg_isready -U communitypulse

# 3. Run full restore (creates everything from scratch)
./database/scripts/restore/full_restore.sh

# 4. (Optional) Load demo data
./database/scripts/restore/load_demo_data.sh
```

## Folder Structure

```
database/
├── README.md                 # This file
├── backups/                  # Backup files (.sql, .dump)
│   ├── .gitkeep
│   └── README.md
├── ddl/                      # Data Definition Language (schema)
│   ├── 00_extensions.sql     # PostgreSQL extensions
│   ├── 01_enums/             # Custom enum types
│   ├── 02_tables/            # Table definitions
│   ├── 03_indexes/           # Index definitions
│   ├── 04_constraints/       # Foreign keys, unique constraints
│   └── README.md
├── dml/                      # Data Manipulation Language (data)
│   ├── seed/                 # Demo/test seed data
│   ├── reference/            # Reference/lookup data
│   └── README.md
├── permissions/              # Roles, users, grants
│   ├── 01_roles.sql
│   ├── 02_grants.sql
│   └── README.md
├── objects/                  # Database objects
│   ├── functions/            # Stored functions
│   ├── triggers/             # Triggers
│   ├── views/                # Views
│   └── README.md
├── scripts/                  # Shell scripts
│   ├── backup/               # Backup scripts
│   ├── restore/              # Restore scripts
│   ├── maintenance/          # Maintenance scripts
│   └── README.md
└── docker/                   # Docker-specific configs
    ├── init/                 # Init scripts for fresh container
    └── README.md
```

## Backup Strategy

### Full Backup
```bash
./database/scripts/backup/full_backup.sh
```
Creates a complete `pg_dump` with schema and data.

### Schema-Only Backup
```bash
./database/scripts/backup/schema_backup.sh
```
Exports only DDL (schema structure).

### Data-Only Backup
```bash
./database/scripts/backup/data_backup.sh
```
Exports only DML (table data).

## Restore Strategy

### Full Restore (Fresh Machine)
```bash
./database/scripts/restore/full_restore.sh
```
Runs all DDL, permissions, and optionally loads seed data.

### Restore from Backup File
```bash
./database/scripts/restore/restore_from_backup.sh database/backups/backup_2026-02-12.sql
```

## Environment Variables

Required in `.env` or shell:
```bash
POSTGRES_USER=communitypulse
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=communitypulse
POSTGRES_HOST=localhost  # or 'db' in Docker network
POSTGRES_PORT=5432
```

## Migration Notes

This project uses Alembic for schema migrations during development.
These SQL scripts are the "frozen" version for backup/restore purposes.

To apply migrations instead:
```bash
docker compose exec api alembic upgrade head
```

## Files NOT in Git

- `backups/*.sql` - Actual backup files (may contain sensitive data)
- `backups/*.dump` - Binary backup files

Add these to `.gitignore` if not already present.
