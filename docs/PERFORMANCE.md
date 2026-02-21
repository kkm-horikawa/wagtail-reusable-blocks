# Performance Guide

wagtail-reusable-blocks is designed for high performance. This guide covers benchmarks, optimization strategies, and best practices.

## Benchmark Results

Performance benchmarks (measured on typical development hardware):

### Rendering Performance

| Operation | Time | Target |
|-----------|------|--------|
| Single block render | ~16us | < 5ms |
| 10 blocks render | ~160us | < 50ms |

### Database Queries

| Operation | Time |
|-----------|------|
| Fetch single block | ~130us |
| Fetch 100 blocks | ~1.4ms |
| Search blocks | ~320us |

### Admin Operations

| Operation | Time |
|-----------|------|
| List with ordering | ~780us |
| List with search | ~860us |
| List with date filter | ~830us |

## N+1 Query Prevention

wagtail-reusable-blocks is optimized to avoid N+1 query issues:

- Rendering 10 blocks uses < 20 queries (not 10+ queries)
- Admin list view uses < 5 queries for 100 blocks
- Uses `select_related()` for foreign key relationships

### Verifying N+1 Prevention

```python
from django.db import connection, reset_queries
from django.conf import settings

settings.DEBUG = True
reset_queries()

# Render multiple blocks
for block in ReusableBlock.objects.all()[:10]:
    block.render()

print(f"Queries: {len(connection.queries)}")
# Should be < 20, not 10+
```

## Optimization Strategies

### 1. Optimize Template Rendering

If using custom templates, keep them simple:

```html
{# Good: Simple template #}
<div class="block">{{ block.content }}</div>

{# Avoid: Complex template with many includes #}
<div class="block">
    {% include "header.html" %}
    {% include "sidebar.html" %}
    {{ block.content }}
    {% include "footer.html" %}
</div>
```

### 2. Limit Nesting Depth

Deep nesting impacts performance:

```python
WAGTAIL_REUSABLE_BLOCKS = {
    'MAX_NESTING_DEPTH': 3,  # Reduce from default 5
}
```

### 3. Prefetch Related Data

When querying multiple blocks:

```python
# Good: Prefetch related data
blocks = ReusableBlock.objects.select_related(
    'locked_by',
    'latest_revision'
).all()

# Avoid: Multiple queries
blocks = ReusableBlock.objects.all()
for block in blocks:
    print(block.locked_by)  # N+1 query!
```

### 4. Use Django's Built-in Caching

For caching rendered blocks, use Django's standard caching mechanisms:

```python
# Template fragment caching
{% load cache %}
{% cache 3600 reusable_block block.pk %}
    {% include_block block %}
{% endcache %}
```

Or use Django's cache middleware for full-page caching.

## Running Benchmarks

### Install pytest-benchmark

```bash
pip install pytest-benchmark
```

### Run Benchmark Tests

```bash
# Run all benchmarks
pytest tests/test_benchmarks.py --benchmark-only -v

# Run specific benchmark group
pytest tests/test_benchmarks.py -k "rendering" --benchmark-only -v

# Compare with baseline
pytest tests/test_benchmarks.py --benchmark-compare
```

### Benchmark Groups

- `rendering` - Block rendering performance
- `queries` - Database query performance
- `admin` - Admin UI query performance

## Monitoring in Production

### Django Debug Toolbar

Install and configure for development:

```python
# settings/dev.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Query Logging

Enable query logging temporarily:

```python
import logging
logging.getLogger('django.db.backends').setLevel(logging.DEBUG)
```

### Performance Profiling

Use Django Silk or similar for production profiling:

```python
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']
```

## Performance Targets

wagtail-reusable-blocks aims to meet these targets:

| Metric | Target | Notes |
|--------|--------|-------|
| Single block render | < 5ms | Direct rendering |
| Page with 10 blocks | < 50ms | Additional overhead |
| Admin list (1000 blocks) | < 500ms | With pagination |
| N+1 queries | 0 | All operations |

## Troubleshooting

### Slow Rendering

1. Review template complexity
2. Check nesting depth
3. Profile with Django Debug Toolbar
4. Consider Django's template fragment caching

### High Query Count

1. Check for N+1 patterns
2. Use `select_related()` / `prefetch_related()`
3. Review admin customizations
