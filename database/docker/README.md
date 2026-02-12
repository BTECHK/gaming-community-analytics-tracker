# Docker Database Configuration

Docker-specific database initialization and configuration files.

## Folders

### init/
Scripts that run automatically when PostgreSQL container starts for the first time.

**Note:** These scripts ONLY run on first container initialization (when `postgres_data` volume is empty).

## Usage

### First Time Setup
```bash
# Start fresh (removes existing volume)
docker compose down -v
docker compose up -d db

# Init scripts run automatically on first start
# Check logs:
docker compose logs db
```

### Reset to Fresh State
```bash
# Remove volumes and restart
docker compose down -v
docker compose up -d db
```

## File Execution Order

PostgreSQL Docker image runs init scripts in alphabetical order:
1. `01_create_extensions.sql`
2. `02_create_schema.sql`
3. `03_create_roles.sql`

## Environment Variables

The init scripts use these environment variables from `docker-compose.yml`:
- `POSTGRES_USER` - Main database user
- `POSTGRES_PASSWORD` - User password
- `POSTGRES_DB` - Database name

## Important Notes

1. Init scripts only run once (on volume creation)
2. To re-run, delete the volume: `docker compose down -v`
3. For ongoing schema changes, use Alembic migrations
4. These scripts provide a "clean slate" for new installations
