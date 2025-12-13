# wagtail-reusable-blocks

[![PyPI version](https://badge.fury.io/py/wagtail-reusable-blocks.svg)](https://badge.fury.io/py/wagtail-reusable-blocks)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/wagtail-reusable-blocks/)
[![CI](https://github.com/kkm-horikawa/wagtail-reusable-blocks/actions/workflows/ci.yml/badge.svg)](https://github.com/kkm-horikawa/wagtail-reusable-blocks/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kkm-horikawa/wagtail-reusable-blocks/branch/develop/graph/badge.svg)](https://codecov.io/gh/kkm-horikawa/wagtail-reusable-blocks)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

## Philosophy

> "The best user interface for a programmer is usually a programming language."
> — [The Zen of Wagtail](https://docs.wagtail.org/en/stable/getting_started/the_zen_of_wagtail.html)

We wholeheartedly embrace Wagtail's philosophy. Wagtail provides powerful systems like StreamField and StructBlock while keeping the core lightweight—free from features that may be unnecessary for some users. Many developers choose Wagtail over WordPress precisely because of this design philosophy.

However, through building Wagtail sites, we discovered a practical limitation: **Wagtail excels at repository-level implementation, but the admin interface can become rigid** when dealing with shared layouts.

For example, if you create a block for a sidebar or header used across pages, it becomes difficult to customize portions of that block on a per-page basis. As we focused more on UX, we noticed our block definitions multiplying and field counts exploding.

This led to a realization: **Just as code is the best interface for developers, HTML is the most flexible interface for content layouts in the admin.** If editors could write flexible layouts in HTML and inject dynamic content (images, rich text) into specific areas, that would be the ultimate Wagtail editing experience.

That's why we built this library.

Programmers want to keep their repositories clean. They don't want to modify block definitions and risk deployments for minor layout tweaks. With wagtail-reusable-blocks, you can bring the flexibility of programming—Wagtail's core strength—directly into the admin interface.

**Write layouts in HTML. Fill slots with content. Deploy zero code changes.**

## Key Features

- ✅ **Zero-code setup** - Works out of the box, no configuration required
- ✅ **Searchable** - Built-in search in snippet chooser modal
- ✅ **Nested blocks** - Reusable blocks can contain other reusable blocks
- ✅ **Circular reference detection** - Prevents infinite loops automatically
- ✅ **Auto-generated slugs** - Slugs created automatically from names
- ✅ **Admin UI** - Search, filter, copy, and inspect blocks
- ✅ **StreamField support** - RichTextBlock and RawHTMLBlock by default
- ✅ **Customizable** - Extend with your own block types
- ✅ **Slot-based templating** (v0.2.0+) - Reusable layouts with fillable slots
- ✅ **Dynamic slot selection** (v0.2.0+) - Auto-populated dropdown for slot IDs
- ✅ **Revision history** (v0.3.0+) - Track changes and restore previous versions
- ✅ **Draft/Publish workflow** (v0.3.0+) - Save drafts before publishing
- ✅ **Locking** (v0.3.0+) - Prevent concurrent editing conflicts
- ✅ **Approval workflows** (v0.3.0+) - Integration with Wagtail workflows

## Use Cases

### Content Reusability (v0.1.0+)
- **Headers/Footers**: Create once, use on all pages
- **Call-to-Action blocks**: Consistent CTAs across the site
- **Promotional banners**: Update in one place, reflect everywhere
- **Disclaimers**: Legal text that needs to be consistent
- **Contact forms**: Reusable form blocks

### Layout Reusability (v0.2.0+)
- **Page templates**: Two-column, three-column, hero sections
- **Card grids**: Product cards, team member cards, feature highlights
- **Article layouts**: Consistent article structure with custom content per page
- **Landing page sections**: Reusable section layouts with page-specific content

## Installation

```bash
pip install wagtail-reusable-blocks
```

Add to your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'wagtail_reusable_blocks',
    # ...
]
```

Run migrations:

```bash
python manage.py migrate
```

That's it! **Reusable Blocks** will now appear in your Wagtail admin under **Snippets**.

### Enhanced HTML Editing (Optional)

For a VS Code-like HTML editing experience with syntax highlighting, Emmet support, and fullscreen mode, install with the `editor` extra:

```bash
pip install wagtail-reusable-blocks[editor]
```

Then add `wagtail_html_editor` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'wagtail_reusable_blocks',
    'wagtail_html_editor',  # Add this for enhanced HTML editing
    # ...
]
```

This enables [wagtail-html-editor](https://github.com/kkm-horikawa/wagtail-html-editor) for all HTML blocks with syntax highlighting, Emmet abbreviations, and fullscreen mode.

## Quick Start

### 1. Create a Reusable Block

1. Go to **Snippets > Reusable Blocks** in Wagtail admin
2. Click **Add Reusable Block**
3. Enter a name (slug is auto-generated)
4. Add content using RichTextBlock or RawHTMLBlock
5. Save

### 2. Use in Your Page Model

```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel
from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

class HomePage(Page):
    body = StreamField([
        ('reusable_block', ReusableBlockChooserBlock()),
        # ... other blocks
    ], blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]
```

### 3. Render in Template

```html
{% load wagtailcore_tags %}

{% for block in page.body %}
    {% include_block block %}
{% endfor %}
```

That's it! The reusable block content will be rendered automatically.

## Choosing the Right Block

wagtail-reusable-blocks provides two block types for different use cases:

### ReusableBlockChooserBlock - Content Reusability (v0.1.0+)

**Use when:** You want to insert finished content that's shared across pages.

**Example:** A promotional banner that appears on multiple pages.

```python
from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

body = StreamField([
    ('reusable_block', ReusableBlockChooserBlock()),
])
```

**Workflow:**
1. Create a ReusableBlock with complete content (text, images, CTAs)
2. Insert it into multiple pages
3. Update the block once, all pages reflect the change

**Best for:**
- Site-wide announcements
- Consistent call-to-action sections
- Legal disclaimers
- Contact information blocks

### ReusableLayoutBlock - Layout Reusability (v0.2.0+)

**Use when:** You want to reuse a layout template and fill it with page-specific content.

**Example:** A two-column layout where the sidebar is fixed but main content varies by page.

```python
from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

body = StreamField([
    ('layout', ReusableLayoutBlock()),
])
```

**Workflow:**
1. Create a ReusableBlock with layout HTML containing `data-slot` attributes
2. Select the layout in your page
3. Fill each slot with page-specific content
4. Layout updates affect all pages, but content remains unique

**Best for:**
- Page templates (two-column, three-column, hero sections)
- Card grids with custom content per card
- Article layouts with consistent structure
- Landing page sections

**Important:** You need to include the app's URLs for slot detection to work:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... other URL patterns
    path('admin/reusable-blocks/', include('wagtail_reusable_blocks.urls')),
    # ... wagtail URLs
]
```

## Slot-Based Templating Tutorial

### 1. Create a Layout Template

Go to **Snippets > Reusable Blocks** and create a new block:

**Name:** Two Column Layout

**Content:** Add an HTML block:

```html
<div class="container">
  <div class="row">
    <aside class="col-md-4">
      <nav class="sidebar-nav">
        <!-- Fixed navigation -->
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/about/">About</a></li>
        </ul>
      </nav>

      <!-- Slot for custom sidebar content -->
      <div data-slot="sidebar-extra" data-slot-label="Extra Sidebar Content">
        <p>Default sidebar content</p>
      </div>
    </aside>

    <main class="col-md-8">
      <!-- Slot for main content -->
      <div data-slot="main" data-slot-label="Main Content">
        <p>Default main content</p>
      </div>
    </main>
  </div>
</div>
```

**Slot attributes** (custom HTML attributes defined by this library):
- `data-slot="slot-id"` - **Required.** Unique identifier (e.g., "main", "sidebar-extra")
- `data-slot-label="Display Name"` - **Optional.** Human-readable label shown in admin
- Child elements - **Optional.** Default content displayed if slot is not filled

### 2. Use the Layout in a Page

```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel
from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

class ArticlePage(Page):
    body = StreamField([
        ('layout', ReusableLayoutBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]
```

### 3. Fill Slots with Content

In the Wagtail admin page editor:

1. Add a "Reusable Layout" block to the body
2. Select "Two Column Layout" from the layout chooser
3. **Automatically**, the available slots appear as dropdowns:
   - Slot: **Main Content** (dropdown)
   - Slot: **Extra Sidebar Content** (dropdown)
4. Select "Main Content" and add your content:
   - Rich Text: "This is my article about..."
   - Image: article-image.jpg
5. Select "Extra Sidebar Content" and add:
   - HTML: `<div class="ad">Advertisement</div>`
6. Publish!

### 4. Render in Template

```django
{% load wagtailcore_tags %}

{% for block in page.body %}
    {% include_block block %}
{% endfor %}
```

The layout HTML is rendered with your slot content injected at the correct positions.

### 5. Advanced: Nesting Layouts

You can nest layouts within slots:

**Outer Layout:** Page wrapper with header/footer slots
**Inner Layout:** Article layout with sidebar/main slots

```python
ReusableLayoutBlock: "Page Wrapper"
├─ slot: "header"
│  └─ ReusableBlockChooserBlock: "Site Header"
├─ slot: "content"
│  └─ ReusableLayoutBlock: "Two Column Layout"  # Nested!
│     ├─ slot: "sidebar-extra"
│     │  └─ HTML: "<div>Ads</div>"
│     └─ slot: "main"
│        └─ RichTextBlock: "Article content..."
└─ slot: "footer"
   └─ ReusableBlockChooserBlock: "Site Footer"
```

## Configuration

All settings are optional. Configure via `WAGTAIL_REUSABLE_BLOCKS` in your Django settings:

```python
# settings.py
WAGTAIL_REUSABLE_BLOCKS = {
    # v0.1.0 settings
    'TEMPLATE': 'my_app/custom_template.html',
    'REGISTER_DEFAULT_SNIPPET': True,
    'MAX_NESTING_DEPTH': 5,

    # v0.2.0 settings
    'SLOT_ATTRIBUTE': 'data-slot',
    'SLOT_LABEL_ATTRIBUTE': 'data-slot-label',
    'RENDER_TIMEOUT': 5,

    # v0.3.0 settings
    'CACHE_ENABLED': True,
    'CACHE_TIMEOUT': 3600,  # 1 hour
    'CACHE_KEY_PREFIX': 'reusable_block',
}
```

### Available Settings

| Setting | Default | Description | Version |
|---------|---------|-------------|---------|
| `TEMPLATE` | `'wagtail_reusable_blocks/reusable_block.html'` | Template used to render blocks | v0.1.0+ |
| `REGISTER_DEFAULT_SNIPPET` | `True` | Auto-register default ReusableBlock snippet | v0.1.0+ |
| `MAX_NESTING_DEPTH` | `5` | Maximum depth for nested reusable blocks | v0.1.0+ |
| `SLOT_ATTRIBUTE` | `'data-slot'` | HTML attribute for slot detection | v0.2.0+ |
| `SLOT_LABEL_ATTRIBUTE` | `'data-slot-label'` | Optional label attribute for slots | v0.2.0+ |
| `RENDER_TIMEOUT` | `5` | Maximum render time in seconds | v0.2.0+ |
| `CACHE_ENABLED` | `False` | Enable caching for rendered blocks | v0.3.0+ |
| `CACHE_TIMEOUT` | `3600` | Cache TTL in seconds (1 hour default) | v0.3.0+ |
| `CACHE_KEY_PREFIX` | `'reusable_block'` | Prefix for cache keys | v0.3.0+ |

## Advanced Usage

### Custom Block Types

To add more block types (images, videos, etc.), create your own model:

```python
from wagtail.blocks import CharBlock, ImageChooserBlock
from wagtail.fields import StreamField
from wagtail.snippets.models import register_snippet
from wagtail_reusable_blocks.models import ReusableBlock

@register_snippet
class CustomReusableBlock(ReusableBlock):
    content = StreamField([
        ('rich_text', RichTextBlock()),
        ('raw_html', RawHTMLBlock()),
        ('image', ImageChooserBlock()),
        ('heading', CharBlock()),
    ], use_json_field=True, blank=True)

    class Meta(ReusableBlock.Meta):
        verbose_name = "Custom Reusable Block"
```

Then disable the default snippet:

```python
# settings.py
WAGTAIL_REUSABLE_BLOCKS = {
    'REGISTER_DEFAULT_SNIPPET': False,
}
```

### Nested Blocks

Reusable blocks can contain other reusable blocks:

1. Create a `ReusableBlock` with your content
2. Create another `ReusableBlock` that references the first one
3. Use the second block in your pages

**Note**: Circular references are automatically detected and prevented. If Block A references Block B, and you try to make Block B reference Block A, you'll get a validation error.

### Custom Templates

Override the default template by creating your own:

```html
{# templates/my_app/custom_block.html #}
<div class="reusable-block">
    {{ block.content }}
</div>
```

Then configure it:

```python
WAGTAIL_REUSABLE_BLOCKS = {
    'TEMPLATE': 'my_app/custom_block.html',
}
```

Or specify per-render:

```python
block.render(template='my_app/custom_block.html')
```

## Troubleshooting

### Circular Reference Error

**Error**: `Circular reference detected: Layout A → Layout B → Layout A`

**Cause**: You've created a circular reference where layouts reference each other in a loop.

**Solution**: Remove one of the references to break the cycle. The error message shows the exact reference chain.

Example fix:
```
Before (circular):
Layout A → slot → Layout B → slot → Layout A ❌

After (linear):
Layout A → slot → Layout B → slot → Layout C ✅
```

### Maximum Nesting Depth Exceeded

**Warning**: `Maximum nesting depth of 5 exceeded`

**Cause**: You've nested layouts deeper than the configured limit (default: 5 levels).

**Solution**:
1. **Reduce nesting depth** - Simplify your layout structure
2. **Increase limit** (not recommended beyond 10):
   ```python
   # settings.py
   WAGTAIL_REUSABLE_BLOCKS = {
       'MAX_NESTING_DEPTH': 10,  # Increase with caution
   }
   ```
3. **Refactor** - Consider whether deep nesting is necessary

### Slots Not Appearing (v0.2.0+)

**Issue**: Selected a layout but no slot fields appear in the editor.

**Solutions**:
1. Ensure you've included the app's URLs in your project:
   ```python
   # urls.py
   urlpatterns = [
       path('admin/reusable-blocks/', include('wagtail_reusable_blocks.urls')),
   ]
   ```
2. Check browser console for JavaScript errors
3. Verify the layout has `data-slot` attributes in its HTML
4. Clear browser cache and reload (Cmd+Shift+R or Ctrl+Shift+R)

### Slot Content Not Rendering (v0.2.0+)

**Issue**: Filled a slot but content doesn't appear on the page.

**Solutions**:
1. Check that the `slot_id` matches the `data-slot` attribute exactly (case-sensitive)
2. Verify you're using `{% include_block block %}` in your template
3. Inspect the rendered HTML - the slot element should contain your content
4. Check browser developer tools for any JavaScript errors

### Slot Dropdown Shows Wrong Slots (v0.2.0+)

**Issue**: Slot dropdown shows slots from a different layout.

**Solutions**:
1. This is a caching issue - refresh the page
2. If persists, clear browser cache
3. Check browser console for API errors
4. Verify the slot detection endpoint is accessible: `/admin/reusable-blocks/blocks/{id}/slots/`

### Search Not Working

**Issue**: Created blocks don't appear in search

**Solution**: Run `python manage.py update_index` to rebuild the search index. New blocks are automatically indexed on save.

## Requirements

| Python | Django | Wagtail |
|--------|--------|---------|
| 3.10+ | 4.2, 5.1, 5.2 | 6.4, 7.0, 7.2 |

See our [CI configuration](.github/workflows/ci.yml) for the complete compatibility matrix.

## Documentation

- [Architecture & Design Decisions](docs/ARCHITECTURE.md)
- [Glossary of Terms](docs/GLOSSARY.md)
- [Caching Guide](docs/CACHING.md) (v0.3.0+)
- [Revisions & Workflows](docs/REVISIONS.md) (v0.3.0+)
- [Performance Guide](docs/PERFORMANCE.md) (v0.3.0+)
- [Contributing Guide](CONTRIBUTING.md)

## Project Links

- [GitHub Repository](https://github.com/kkm-horikawa/wagtail-reusable-blocks)
- [Project Board](https://github.com/users/kkm-horikawa/projects/6)
- [Issue Tracker](https://github.com/kkm-horikawa/wagtail-reusable-blocks/issues)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.

## Inspiration

- [WordPress Gutenberg Synced Patterns](https://wordpress.org/documentation/article/reusable-blocks/)
- [Wagtail CRX Reusable Content](https://docs.coderedcorp.com/wagtail-crx/features/snippets/reusable_content.html)
- [React Slots and Composition](https://react.dev/learn/passing-props-to-a-component)
