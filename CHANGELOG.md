# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
