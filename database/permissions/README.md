# Permissions

Database roles, users, and access grants.

## Files

- `01_roles.sql` - Role definitions (app user, readonly, admin)
- `02_grants.sql` - Permission grants to roles

## Execution Order

1. Run `01_roles.sql` first (creates roles)
2. Run `02_grants.sql` second (grants permissions)

## Usage

```bash
# From project root:
docker compose exec -T db psql -U communitypulse -d communitypulse < database/permissions/01_roles.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/permissions/02_grants.sql
```

## Role Descriptions

### communitypulse (Application User)
- Primary application connection user
- Full CRUD access to all tables
- Cannot create/drop tables (use migrations)

### communitypulse_readonly
- Read-only access for reporting/analytics
- SELECT only on all tables
- Safe for dashboards and external tools

### communitypulse_admin
- Superuser-equivalent for this database
- Full DDL access (create/drop)
- Use sparingly, mainly for migrations

## Environment Notes

- In Docker development: Uses `communitypulse` user by default
- In production: Create separate users inheriting these roles
- Never share production credentials in code/git
