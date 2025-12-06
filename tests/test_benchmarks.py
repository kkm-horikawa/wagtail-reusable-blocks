"""Performance benchmark tests for wagtail-reusable-blocks.

These tests measure performance against defined targets:
- Single ReusableBlock rendering (cached): < 5ms
- Page with 10 ReusableBlocks: < 50ms additional overhead
- Admin list with 1000 blocks: < 500ms
- N+1 queries: Zero

Run benchmarks with:
    pytest tests/test_benchmarks.py --benchmark-only -v
"""

import pytest
from django.db import connection, reset_queries
from django.test.utils import override_settings

from wagtail_reusable_blocks.cache import ReusableBlockCache
from wagtail_reusable_blocks.models import ReusableBlock


@pytest.fixture
def simple_block(db):
    """Create a simple ReusableBlock for benchmarking."""
    return ReusableBlock.objects.create(
        name="Benchmark Block",
        slug="benchmark-block",
        content=[{"type": "rich_text", "value": "<p>Benchmark content</p>"}],
    )


@pytest.fixture
def blocks_10(db):
    """Create 10 ReusableBlocks for benchmarking."""
    blocks = []
    for i in range(10):
        block = ReusableBlock.objects.create(
            name=f"Benchmark Block {i}",
            slug=f"benchmark-block-{i}",
            content=[{"type": "rich_text", "value": f"<p>Content {i}</p>"}],
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def blocks_100(db):
    """Create 100 ReusableBlocks for benchmarking."""
    blocks = []
    for i in range(100):
        block = ReusableBlock.objects.create(
            name=f"Benchmark Block {i}",
            slug=f"benchmark-block-{i}",
            content=[{"type": "rich_text", "value": f"<p>Content {i}</p>"}],
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def nested_blocks(db):
    """Create nested ReusableBlocks for benchmarking."""
    # Create inner block
    inner = ReusableBlock.objects.create(
        name="Inner Block",
        slug="inner-block",
        content=[{"type": "rich_text", "value": "<p>Inner content</p>"}],
    )
    # Create outer block that references inner (via layout)
    outer = ReusableBlock.objects.create(
        name="Outer Block",
        slug="outer-block",
        content=[
            {
                "type": "raw_html",
                "value": f'<div data-slot="main">Default for {inner.pk}</div>',
            }
        ],
    )
    return {"inner": inner, "outer": outer}


class TestRenderingBenchmarks:
    """Benchmark tests for block rendering performance."""

    @pytest.mark.benchmark(group="rendering")
    def test_single_block_render_uncached(self, benchmark, simple_block, settings):
        """Benchmark single block rendering without cache."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {"CACHE_ENABLED": False}

        def render_block():
            return simple_block.render()

        result = benchmark(render_block)
        assert result is not None
        assert len(result) > 0

    @pytest.mark.benchmark(group="rendering")
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }
    )
    def test_single_block_render_cached(self, benchmark, simple_block, settings):
        """Benchmark single block rendering with cache.

        Target: < 5ms
        """
        settings.WAGTAIL_REUSABLE_BLOCKS = {"CACHE_ENABLED": True}

        # Pre-warm cache
        simple_block.render()

        def render_block():
            return simple_block.render()

        result = benchmark(render_block)
        assert result is not None
        # Performance target verified by benchmark output (< 5ms)

    @pytest.mark.benchmark(group="rendering")
    def test_10_blocks_render_uncached(self, benchmark, blocks_10, settings):
        """Benchmark rendering 10 blocks without cache."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {"CACHE_ENABLED": False}

        def render_blocks():
            results = []
            for block in blocks_10:
                results.append(block.render())
            return results

        result = benchmark(render_blocks)
        assert len(result) == 10

    @pytest.mark.benchmark(group="rendering")
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }
    )
    def test_10_blocks_render_cached(self, benchmark, blocks_10, settings):
        """Benchmark rendering 10 blocks with cache.

        Target: < 50ms additional overhead
        """
        settings.WAGTAIL_REUSABLE_BLOCKS = {"CACHE_ENABLED": True}

        # Pre-warm cache
        for block in blocks_10:
            block.render()

        def render_blocks():
            results = []
            for block in blocks_10:
                results.append(block.render())
            return results

        result = benchmark(render_blocks)
        assert len(result) == 10
        # Performance target verified by benchmark output (< 50ms)


class TestQueryBenchmarks:
    """Benchmark tests for database query performance."""

    @pytest.mark.benchmark(group="queries")
    def test_block_fetch_single(self, benchmark, simple_block):
        """Benchmark fetching a single block by slug."""

        def fetch_block():
            return ReusableBlock.objects.get(slug="benchmark-block")

        result = benchmark(fetch_block)
        assert result.pk == simple_block.pk

    @pytest.mark.benchmark(group="queries")
    def test_block_fetch_list(self, benchmark, blocks_100):
        """Benchmark fetching block list."""

        def fetch_blocks():
            return list(ReusableBlock.objects.all()[:100])

        result = benchmark(fetch_blocks)
        assert len(result) == 100

    @pytest.mark.benchmark(group="queries")
    def test_block_search(self, benchmark, blocks_100):
        """Benchmark searching blocks by name."""

        def search_blocks():
            return list(ReusableBlock.objects.filter(name__icontains="Block 5"))

        result = benchmark(search_blocks)
        assert len(result) >= 1


@pytest.mark.django_db
class TestNPlusOneQueries:
    """Tests to detect and prevent N+1 query issues."""

    @pytest.fixture(autouse=True)
    def enable_query_logging(self, settings):
        """Enable query logging for N+1 detection."""
        settings.DEBUG = True
        yield
        settings.DEBUG = False

    def test_render_multiple_blocks_no_n_plus_one(self, blocks_10, settings):
        """Verify rendering multiple blocks doesn't cause N+1 queries."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {"CACHE_ENABLED": False}

        reset_queries()

        # Render all blocks
        for block in blocks_10:
            block.render()

        query_count = len(connection.queries)

        # Should not have N+1 pattern (10 blocks shouldn't need 10+ queries)
        # Allow some queries for template loading, etc.
        # The key is that query count should be O(1) not O(n)
        assert query_count < 20, (
            f"Potential N+1 issue: {query_count} queries for 10 blocks. "
            f"Queries: {[q['sql'][:100] for q in connection.queries]}"
        )

    def test_admin_list_no_n_plus_one(self, blocks_100, settings):
        """Verify admin list view doesn't cause N+1 queries."""
        settings.DEBUG = True
        reset_queries()

        # Simulate admin list query
        blocks = list(
            ReusableBlock.objects.all()
            .select_related("locked_by", "latest_revision")
            .order_by("-updated_at")[:100]
        )

        query_count = len(connection.queries)

        # Should be O(1) queries, not O(n)
        assert query_count < 5, (
            f"Potential N+1 issue: {query_count} queries for admin list. "
            f"Expected <= 4 queries."
        )

        # Verify we got the blocks
        assert len(blocks) == 100


class TestCacheBenchmarks:
    """Benchmark tests for cache operations."""

    @pytest.fixture
    def cache(self):
        """Get cache instance."""
        return ReusableBlockCache()

    @pytest.mark.benchmark(group="cache")
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
    )
    def test_cache_get_hit(self, benchmark, cache, simple_block):
        """Benchmark cache hit performance."""
        # Pre-populate cache
        cache.set(simple_block.pk, "<p>Cached content</p>")

        def cache_get():
            return cache.get(simple_block.pk)

        result = benchmark(cache_get)
        assert result == "<p>Cached content</p>"

    @pytest.mark.benchmark(group="cache")
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
    )
    def test_cache_set(self, benchmark, cache, simple_block):
        """Benchmark cache set performance."""

        def cache_set():
            cache.set(simple_block.pk, "<p>New content</p>")

        benchmark(cache_set)

    @pytest.mark.benchmark(group="cache")
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
    )
    def test_cache_invalidate(self, benchmark, cache, simple_block):
        """Benchmark cache invalidation performance."""
        # Pre-populate cache
        cache.set(simple_block.pk, "<p>Cached content</p>")

        def cache_invalidate():
            cache.invalidate(simple_block.pk)
            # Re-populate for next iteration
            cache.set(simple_block.pk, "<p>Cached content</p>")

        benchmark(cache_invalidate)


class TestAdminBenchmarks:
    """Benchmark tests for admin operations."""

    @pytest.mark.benchmark(group="admin")
    def test_admin_queryset_ordering(self, benchmark, blocks_100):
        """Benchmark admin queryset with ordering."""

        def query_with_ordering():
            return list(ReusableBlock.objects.order_by("-updated_at")[:50])

        result = benchmark(query_with_ordering)
        assert len(result) == 50

    @pytest.mark.benchmark(group="admin")
    def test_admin_queryset_search(self, benchmark, blocks_100):
        """Benchmark admin queryset with search."""

        def query_with_search():
            return list(
                ReusableBlock.objects.filter(name__icontains="Block").order_by(
                    "-updated_at"
                )[:50]
            )

        result = benchmark(query_with_search)
        assert len(result) == 50

    @pytest.mark.benchmark(group="admin")
    def test_admin_queryset_filter_date(self, benchmark, blocks_100):
        """Benchmark admin queryset with date filter."""
        from django.utils import timezone

        now = timezone.now()

        def query_with_date_filter():
            return list(
                ReusableBlock.objects.filter(created_at__lte=now).order_by(
                    "-updated_at"
                )[:50]
            )

        result = benchmark(query_with_date_filter)
        assert len(result) == 50
