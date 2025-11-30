# wagtail-reusable-blocks

[![PyPI version](https://badge.fury.io/py/wagtail-reusable-blocks.svg)](https://badge.fury.io/py/wagtail-reusable-blocks)
[![CI](https://github.com/kkm-horikawa/wagtail-reusable-blocks/actions/workflows/ci.yml/badge.svg)](https://github.com/kkm-horikawa/wagtail-reusable-blocks/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kkm-horikawa/wagtail-reusable-blocks/branch/develop/graph/badge.svg)](https://codecov.io/gh/kkm-horikawa/wagtail-reusable-blocks)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

A Wagtail CMS extension for creating **reusable content blocks** that can be shared across multiple pages.

## What is this?

Create content blocks once and reuse them across your Wagtail site. When you update a reusable block, all pages using it automatically reflect the changes.

**Think of it like WordPress Gutenberg's "Synced Patterns" (formerly Reusable Blocks), but for Wagtail.**

## Key Features

- ✅ **Zero-code setup** - Works out of the box, no configuration required
- ✅ **Searchable** - Built-in search in snippet chooser modal
- ✅ **Nested blocks** - Reusable blocks can contain other reusable blocks
- ✅ **Circular reference detection** - Prevents infinite loops automatically
- ✅ **Auto-generated slugs** - Slugs created automatically from names
- ✅ **Admin UI** - Search, filter, copy, and inspect blocks
- ✅ **StreamField support** - RichTextBlock and RawHTMLBlock by default
- ✅ **Customizable** - Extend with your own block types

## Use Cases

- **Headers/Footers**: Create once, use on all pages
- **Call-to-Action blocks**: Consistent CTAs across the site
- **Promotional banners**: Update in one place, reflect everywhere
- **Disclaimers**: Legal text that needs to be consistent
- **Contact forms**: Reusable form blocks

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

## Configuration

All settings are optional. Configure via `WAGTAIL_REUSABLE_BLOCKS` in your Django settings:

```python
# settings.py
WAGTAIL_REUSABLE_BLOCKS = {
    # Template for rendering blocks (default: 'wagtail_reusable_blocks/reusable_block.html')
    'TEMPLATE': 'my_app/custom_template.html',

    # Whether to register the default ReusableBlock snippet (default: True)
    'REGISTER_DEFAULT_SNIPPET': True,

    # Maximum nesting depth for nested blocks (default: 5)
    'MAX_NESTING_DEPTH': 5,
}
```

### Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `TEMPLATE` | `'wagtail_reusable_blocks/reusable_block.html'` | Template used to render blocks |
| `REGISTER_DEFAULT_SNIPPET` | `True` | Auto-register default ReusableBlock snippet |
| `MAX_NESTING_DEPTH` | `5` | Maximum depth for nested reusable blocks |

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

**Error**: `Circular reference detected: Block 'A' references block 'B' which creates a cycle.`

**Cause**: You've created a circular reference where Block A → Block B → Block A.

**Solution**: Remove one of the references to break the cycle. Reusable blocks can be nested, but not in circles.

### Maximum Nesting Depth Exceeded

**Error**: `Maximum nesting depth exceeded` (displayed as a warning in the rendered output)

**Cause**: You've nested reusable blocks deeper than the configured `MAX_NESTING_DEPTH` (default: 5).

**Solution**:
- Reduce nesting depth by refactoring your block structure
- Or increase `MAX_NESTING_DEPTH` in settings (not recommended beyond 10)

### Search Not Working

**Issue**: Created blocks don't appear in search

**Solution**: Run `python manage.py update_index` to rebuild the search index. New blocks are automatically indexed on save.

## Requirements

| Python | Django | Wagtail |
|--------|--------|---------|
| 3.10+ | 4.2, 5.1, 5.2 | 5.2, 6.4, 7.0, 7.2 |

See our [CI configuration](.github/workflows/ci.yml) for the complete compatibility matrix (39 tested combinations).

## Features by Version

### v0.1.0 - MVP (Current)
- ✅ ReusableBlock model with StreamField support
- ✅ ReusableBlockChooserBlock for page integration
- ✅ Admin UI with search, filtering, and copy functionality
- ✅ Nested blocks with circular reference detection
- ✅ Auto-generated slugs
- ✅ Searchable snippet chooser

### v0.2.0 - Slot System (Planned)
- Define placeholders within reusable blocks
- Inject content into slots from page level
- Component composition without code changes

### v0.3.0 - Performance & Polish (Planned)
- Caching for optimized rendering
- Usage tracking ("where is this block used?")
- Revision support

## Documentation

- [Architecture & Design Decisions](docs/ARCHITECTURE.md)
- [Glossary of Terms](docs/GLOSSARY.md)
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
