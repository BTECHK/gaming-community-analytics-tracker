# Database Backups

This folder stores database backup files.

## File Types

- `*.sql` - Plain text SQL dumps (portable, human-readable)
- `*.dump` - PostgreSQL custom format (compressed, faster restore)

## Naming Convention

```
{type}_{database}_{timestamp}.{ext}
```

Examples:
- `full_communitypulse_2026-02-12_143022.sql` - Full backup
- `schema_communitypulse_2026-02-12_143022.sql` - Schema only
- `data_communitypulse_2026-02-12_143022.sql` - Data only

## Creating Backups

Use the scripts in `../scripts/backup/`:

```bash
# Full backup (schema + data)
../scripts/backup/full_backup.sh

# Schema only
../scripts/backup/schema_backup.sh

# Data only
../scripts/backup/data_backup.sh
```

## Important Notes

1. **Do NOT commit sensitive backups to git**
2. Backups with production data should be encrypted
3. Test restores periodically to verify backup integrity
4. Keep multiple backup generations (daily, weekly, monthly)

## .gitignore

Backup files are excluded from git. Only this README is tracked.
