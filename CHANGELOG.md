# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-05

### Added

- **Content Types**
  - Define custom content schemas per tenant
  - JSON Schema stored as JSONB, validated on entry creation with `jsonschema`

- **Content Entries**
  - Create and manage entries scoped to a content type
  - Payload validated against the content type's JSON Schema at write time
  - `created_by` / `updated_by` audit fields
  - Draft/publish workflow with `is_published`

- **Tenant Members**
  - Staff account creation scoped to a tenant via Supabase Admin API
  - Synthetic emails: `{username}@{tenant.slug}.keta.com`
  - Role support: `owner` / `member`

- **Repository Mixins**
  - `PublishableMixin` — composable `is_published` filtering via MRO `_build_conditions` chain
  - `SoftDeleteMixin` — composable soft delete / restore support

### Changed

- `generate_unique_slug` consolidated into `BaseRepository` as single source of truth
  - Removed duplicate implementations from `TenantScopeRepository`, `TenantRepository`, and `ImageRepository`
  - Replaced sequential counter pattern (`-1`, `-2`, ...) with `secrets.token_hex(3)` random suffix — eliminates race condition under concurrent requests
  - Callers pass SQLAlchemy expressions as `*scope_conditions` to define uniqueness scope (e.g. `Album.tenant_id == tenant_id`, `Image.album_id == album_id`)
  - Bounded retry loop (5 attempts) with `uuid4` fallback as last resort

### Fixed

- Race condition in slug generation across Albums, Images, ContentEntries, and Tenants (check-then-act pattern replaced with random suffix + DB constraint as safety net)
- `slugify` corrected from module import to function import in `BaseRepository`
- UUID fallback corrected from `uuid.UUID()` (invalid) to `uuid.uuid4()` in slug generation fallback

### Known Issues

- `SlowAPIMiddleware` not registered in `main.py` — rate limiting decorators are currently no-ops
- `update_account` in `TenantMemberService` passes a Pydantic schema to `repo.update()` instead of the ORM object — member updates do not persist
- `AsyncSession` not imported in `auth/router.py` (unused parameter in `sign_in`)
- No tenant authorization guard — authenticated users can query any `tenant_id` from the URL
- Supabase user not rolled back if local DB sync fails during staff account creation

---

## [0.1.0] - 2026-01-28

### Added

- **Authentication**
  - User signup with email verification (Supabase Auth)
  - User signin with JWT tokens
  - Resend verification email endpoint

- **Events Management**
  - CRUD operations for events
  - Cover image upload to Supabase Storage
  - Auto-generated SEO-friendly slugs
  - Draft/publish workflow

- **Gallery Management**
  - Album CRUD with image collections
  - Bulk image upload with validation (JPEG, PNG, WebP)
  - Auto-generated slugs for SEO
  - Auto-set album cover from first uploaded image

- **Public Endpoints**
  - Public events listing for landing pages
  - Public gallery/albums for portfolios
  - No authentication required for public access

- **Infrastructure**
  - Rate limiting with Upstash Redis
  - Structured logging with structlog
  - Custom exception handling
  - CORS configuration

- **API Documentation**
  - Comprehensive OpenAPI/Swagger docs
  - Rate limit info in endpoint descriptions

### Known Issues

- Storage cleanup on album/image delete not implemented (orphaned files in Supabase Storage)
- Missing tests for gallery feature
- Soft delete not implemented (hard deletes only)

### Tech Stack

- FastAPI + Python 3.11+
- PostgreSQL via Supabase
- Redis via Upstash
- Supabase Auth & Storage
