# Caching Guide

wagtail-reusable-blocks v0.3.0+ includes an optional caching system to improve rendering performance.

## Overview

When caching is enabled, rendered block HTML is stored in Django's cache backend. Subsequent renders retrieve the cached HTML instead of re-rendering, significantly improving performance for frequently accessed blocks.

## Enabling Caching

```python
# settings.py
WAGTAIL_REUSABLE_BLOCKS = {
    'CACHE_ENABLED': True,
    'CACHE_TIMEOUT': 3600,  # 1 hour (default)
    'CACHE_KEY_PREFIX': 'reusable_block',  # default
}
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `CACHE_ENABLED` | `False` | Enable/disable caching |
| `CACHE_TIMEOUT` | `3600` | Cache TTL in seconds |
| `CACHE_KEY_PREFIX` | `'reusable_block'` | Prefix for cache keys |

## Cache Backend

The caching system uses Django's default cache backend. For production, we recommend using Redis or Memcached:

### Redis (Recommended)

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Memcached

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
```

### Local Memory (Development Only)

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## Automatic Cache Invalidation

Cache is automatically invalidated when:

1. **Block is saved** - Any update to a ReusableBlock clears its cache
2. **Block is deleted** - Cache entry is removed
3. **Manual clear** - Via admin UI button or programmatically

### Admin UI

A "Clear Cache" button appears in the snippet listing for each block when caching is enabled.

### Programmatic Invalidation

```python
from wagtail_reusable_blocks.cache import ReusableBlockCache

cache = ReusableBlockCache()

# Clear cache for a specific block
cache.invalidate(block_id)

# Clear all block caches
cache.clear_all()
```

## Cache Key Structure

Cache keys follow this format:
```
{prefix}:{block_id}:{content_hash}
```

Example: `reusable_block:42:a1b2c3d4`

The content hash ensures cache is invalidated when block content changes, even if the block ID remains the same.

## Performance Considerations

### When to Enable Caching

Enable caching when:
- Blocks are rendered frequently across many pages
- Block content doesn't change often
- You have a suitable cache backend (Redis/Memcached)

### When to Avoid Caching

Consider disabling caching when:
- Block content is highly dynamic
- You're in development and frequently editing blocks
- Cache storage is limited

### Cache Timeout Recommendations

| Use Case | Recommended Timeout |
|----------|---------------------|
| Static content (headers, footers) | 86400 (24 hours) |
| Semi-static content | 3600 (1 hour) |
| Frequently updated content | 300 (5 minutes) |

## Monitoring

### Check Cache Status

```python
from wagtail_reusable_blocks.cache import ReusableBlockCache

cache = ReusableBlockCache()

# Check if caching is enabled
print(cache.is_enabled())  # True/False

# Check if a block is cached
cached_content = cache.get(block_id)
if cached_content:
    print("Cache hit!")
else:
    print("Cache miss")
```

## Troubleshooting

### Cache Not Working

1. **Verify caching is enabled**:
   ```python
   from wagtail_reusable_blocks.conf import get_setting
   print(get_setting('CACHE_ENABLED'))  # Should be True
   ```

2. **Check Django cache is configured**:
   ```python
   from django.core.cache import cache
   cache.set('test', 'value', 60)
   print(cache.get('test'))  # Should print 'value'
   ```

3. **Verify cache backend is running** (Redis/Memcached)

### Stale Content

If you see outdated content after updating a block:

1. Clear the block's cache via admin UI
2. Or programmatically:
   ```python
   from wagtail_reusable_blocks.cache import ReusableBlockCache
   ReusableBlockCache().invalidate(block_id)
   ```

### Memory Issues

If using local memory cache with many blocks, consider:
- Switching to Redis/Memcached
- Reducing `CACHE_TIMEOUT`
- Disabling caching for infrequently accessed blocks
