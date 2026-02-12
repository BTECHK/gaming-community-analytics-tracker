# Database Scripts

Shell scripts for backup, restore, and maintenance operations.

## Folders

- `backup/` - Scripts for creating backups
- `restore/` - Scripts for restoring from backups or DDL
- `maintenance/` - Utility scripts for health checks and cleanup

## Prerequisites

- Docker Desktop running
- `docker compose up -d db` (database container)
- Bash shell (Git Bash on Windows, or WSL)

## Quick Reference

### Backup Commands
```bash
# Full backup (schema + data)
./database/scripts/backup/full_backup.sh

# Schema only
./database/scripts/backup/schema_backup.sh

# Data only
./database/scripts/backup/data_backup.sh
```

### Restore Commands
```bash
# Full restore from DDL (fresh database)
./database/scripts/restore/full_restore.sh

# Restore from backup file
./database/scripts/restore/restore_from_backup.sh <backup_file>

# Load demo data only
./database/scripts/restore/load_demo_data.sh
```

### Maintenance Commands
```bash
# Health check
./database/scripts/maintenance/health_check.sh

# Vacuum and analyze
./database/scripts/maintenance/vacuum_analyze.sh

# Show table sizes
./database/scripts/maintenance/table_sizes.sh
```

## Windows Notes

Run scripts from Git Bash or WSL:
```bash
# From Git Bash
cd /c/Users/you/Projects/gaming-community-analytics-tracker
./database/scripts/backup/full_backup.sh
```

Or use the provided `.bat` wrappers (if created).

## Environment Variables

Scripts use these environment variables (with defaults):
```bash
POSTGRES_USER=${POSTGRES_USER:-communitypulse}
POSTGRES_DB=${POSTGRES_DB:-communitypulse}
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
```

Override by exporting before running:
```bash
export POSTGRES_USER=myuser
./database/scripts/backup/full_backup.sh
```
