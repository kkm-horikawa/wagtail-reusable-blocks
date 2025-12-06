# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - TBD

### Added

#### Caching System
- **Render caching** - Optional caching for rendered block HTML
- **Automatic invalidation** - Cache cleared on block save/delete
- **Admin cache clear** - "Clear Cache" button in snippet listing
- Configuration: `CACHE_ENABLED`, `CACHE_TIMEOUT`, `CACHE_KEY_PREFIX`

#### Wagtail Mixins Integration
- **RevisionMixin** - Full revision history with restore capability
- **DraftStateMixin** - Draft/publish workflow support
- **LockableMixin** - Prevent concurrent editing conflicts
- **WorkflowMixin** - Integration with Wagtail approval workflows
- **PreviewableMixin** - Live preview in admin

#### Scheduling
- **Go-live scheduling** - Schedule blocks to publish at specific times
- **Expiry scheduling** - Schedule blocks to unpublish automatically

#### Performance
- **Benchmark test suite** - Comprehensive performance tests with pytest-benchmark
- **N+1 query prevention** - Optimized queries for admin and rendering
- Performance targets: < 5ms single block, < 50ms for 10 blocks

### Documentation

- [Caching Guide](docs/CACHING.md) - Cache configuration and best practices
- [Revisions & Workflows](docs/REVISIONS.md) - Using revision history and workflows
- [Performance Guide](docs/PERFORMANCE.md) - Benchmarks and optimization

### Breaking Changes

**Database migration required!** Run after upgrading:
```bash
python manage.py migrate wagtail_reusable_blocks
```

The migration adds fields for:
- Revision tracking (`latest_revision`)
- Draft state (`live`, `has_unpublished_changes`, `first_published_at`, `last_published_at`)
- Scheduling (`go_live_at`, `expire_at`, `expired`)
- Locking (`locked`, `locked_by`, `locked_at`)

Existing blocks will be migrated with `live=True` and no revision history.

## [0.2.0] - TBD

### Added

#### Slot-Based Templating System
- **ReusableLayoutBlock** - New block type for layout templates with fillable slots
- **SlotFillBlock** - Block for injecting custom content into layout slots
- Slot detection API endpoint (`/admin/reusable-blocks/blocks/{id}/slots/`)
- Dynamic slot selection UI with JavaScript widget
- Automatic slot detection from HTML `data-slot` attributes
- Support for nested layouts (layouts within slots)
- Default content preservation for unfilled slots

#### Developer Experience
- BeautifulSoup4 for robust HTML parsing
- Slot rendering utilities (`render_layout_with_slots`)
- Extended circular reference detection for slot-based nesting
- Improved error messages with reference chains (e.g., "Layout A → Layout B → Layout A")

#### Configuration
- `SLOT_ATTRIBUTE` - Customizable HTML attribute for slots (default: `data-slot`)
- `SLOT_LABEL_ATTRIBUTE` - Optional label attribute (default: `data-slot-label`)
- `RENDER_TIMEOUT` - Maximum render time limit (default: 5 seconds)

### Enhanced

- Circular reference detection now handles slot-based nesting
- Error messages show complete reference chain for easier debugging

### Documentation

- "Choosing the Right Block" guide
- Slot-based templating tutorial with step-by-step examples
- Troubleshooting section for slot-related issues
- Updated ARCHITECTURE.md with slot rendering flow
- Configuration reference updated with v0.2.0 settings

### Breaking Changes

**None!** v0.2.0 is fully backward compatible with v0.1.0.

- Existing `ReusableBlockChooserBlock` continues to work as before
- No database migrations required
- Existing ReusableBlocks work without changes
- v0.1.0 and v0.2.0 blocks can be used together in the same page

### Migration Guide

No migration needed! To start using slot-based templating:

1. **Add URLs** (required for slot detection):
   ```python
   # urls.py
   urlpatterns = [
       path('admin/reusable-blocks/', include('wagtail_reusable_blocks.urls')),
   ]
   ```

2. **Create a layout** with `data-slot` attributes:
   ```html
   <div data-slot="main" data-slot-label="Main Content">
       <p>Default content</p>
   </div>
   ```

3. **Use ReusableLayoutBlock** in your page models:
   ```python
   from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

   body = StreamField([
       ('layout', ReusableLayoutBlock()),
   ])
   ```

That's it! See the [README](README.md) for the complete tutorial.

## [0.1.0] - 2025-01-XX

### Added

#### Core Features
- **ReusableBlock** model with StreamField support
- **ReusableBlockChooserBlock** for page integration
- Admin UI with search, filtering, and copy functionality
- Nested blocks with circular reference detection
- Auto-generated slugs from names
- Searchable snippet chooser

#### Configuration
- `TEMPLATE` - Custom template for rendering blocks
- `REGISTER_DEFAULT_SNIPPET` - Toggle default snippet registration
- `MAX_NESTING_DEPTH` - Maximum depth for nested blocks (default: 5)

#### Developer Experience
- Comprehensive test suite with 95%+ coverage
- CI/CD across 39 Python/Django/Wagtail combinations
- Type hints and documentation
- Contributing guide and code standards

### Documentation

- Comprehensive README with quick start guide
- Architecture documentation (ARCHITECTURE.md)
- Glossary of terms (GLOSSARY.md)
- Contributing guidelines (CONTRIBUTING.md)

[Unreleased]: https://github.com/kkm-horikawa/wagtail-reusable-blocks/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kkm-horikawa/wagtail-reusable-blocks/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kkm-horikawa/wagtail-reusable-blocks/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kkm-horikawa/wagtail-reusable-blocks/releases/tag/v0.1.0
