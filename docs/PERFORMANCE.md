# Performance Guide

wagtail-reusable-blocks is designed for high performance. This guide covers benchmarks, optimization strategies, and best practices.

## Benchmark Results

Performance benchmarks from v0.3.0 (measured on typical development hardware):

### Rendering Performance

| Operation | Time | Target |
|-----------|------|--------|
| Single block render (cached) | ~16μs | < 5ms |
| Single block render (uncached) | ~16μs | < 5ms |
| 10 blocks render (cached) | ~160μs | < 50ms |
| 10 blocks render (uncached) | ~158μs | < 50ms |

### Cache Operations

| Operation | Time |
|-----------|------|
| Cache hit | ~3μs |
| Cache set | ~4μs |
| Cache invalidate | ~6μs |

### Database Queries

| Operation | Time |
|-----------|------|
| Fetch single block | ~130μs |
| Fetch 100 blocks | ~1.4ms |
| Search blocks | ~320μs |

### Admin Operations

| Operation | Time |
|-----------|------|
| List with ordering | ~780μs |
| List with search | ~860μs |
| List with date filter | ~830μs |

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

### 1. Enable Caching (Recommended)

For production, enable caching:

```python
WAGTAIL_REUSABLE_BLOCKS = {
    'CACHE_ENABLED': True,
    'CACHE_TIMEOUT': 3600,
}
```

### 2. Use an Efficient Cache Backend

Redis is recommended for production:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Optimize Template Rendering

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

### 4. Limit Nesting Depth

Deep nesting impacts performance:

```python
WAGTAIL_REUSABLE_BLOCKS = {
    'MAX_NESTING_DEPTH': 3,  # Reduce from default 5
}
```

### 5. Prefetch Related Data

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
- `cache` - Cache operation performance
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
| Single block render (cached) | < 5ms | Including cache lookup |
| Page with 10 blocks | < 50ms | Additional overhead |
| Admin list (1000 blocks) | < 500ms | With pagination |
| N+1 queries | 0 | All operations |

## Troubleshooting

### Slow Rendering

1. Check if caching is enabled
2. Review template complexity
3. Check nesting depth
4. Profile with Django Debug Toolbar

### High Query Count

1. Check for N+1 patterns
2. Use `select_related()` / `prefetch_related()`
3. Review admin customizations

### Cache Misses

1. Verify cache backend is running
2. Check `CACHE_TIMEOUT` setting
3. Monitor cache hit rate

### Memory Issues

1. Reduce `CACHE_TIMEOUT`
2. Use Redis instead of local memory
3. Monitor cache size
