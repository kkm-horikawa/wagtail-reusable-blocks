# wagtail-reusable-blocks

[![PyPI version](https://badge.fury.io/py/wagtail-reusable-blocks.svg)](https://badge.fury.io/py/wagtail-reusable-blocks)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

A Wagtail CMS extension for creating **reusable content blocks** with an advanced **slot-based templating system**.

## What is this?

This package bridges the gap between Wagtail's **Snippets** and **Page Blocks**:

| Feature | Snippets | Page Blocks | **Reusable Blocks** |
|---------|----------|-------------|---------------------|
| Reusable across pages | No | No | **Yes** |
| StreamField support | Limited | Yes | **Yes** |
| Single source of truth | Yes | No | **Yes** |
| Slot/placeholder support | No | No | **Yes (v0.2.0+)** |

**Think of it like WordPress Gutenberg's "Synced Patterns" (formerly Reusable Blocks), but for Wagtail.**

## Use Cases

- **Headers/Footers**: Create once, use on all pages
- **Call-to-Action blocks**: Consistent CTAs across the site
- **Promotional banners**: Update in one place, reflect everywhere
- **Layout templates**: Define page structures with customizable slots
- **Design systems**: Build component libraries for content editors

## Installation

```bash
pip install wagtail-reusable-blocks
```

Add to your `INSTALLED_APPS`:

```python
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

## Quick Start

### 1. Create a Reusable Block

Go to **Snippets > Reusable Blocks** in Wagtail admin and create a new block.

### 2. Use in Your Page Model

```python
from wagtail.fields import StreamField
from wagtail.blocks import RichTextBlock
from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

class MyPage(Page):
    body = StreamField([
        ('rich_text', RichTextBlock()),
        ('reusable_block', ReusableBlockChooserBlock()),
    ], use_json_field=True)
```

### 3. Render in Template

```html
{% for block in page.body %}
    {% include_block block %}
{% endfor %}
```

## Features by Version

### v0.1.0 - MVP (Reusable Blocks)
- ReusableBlock model with StreamField support
- ReusableBlockChooserBlock for page integration
- Admin UI for managing reusable blocks

### v0.2.0 - Slot System
- Define placeholders within reusable blocks
- Inject content into slots from page level
- Component composition without code changes

### v0.3.0 - Performance & Polish
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

## Roadmap

See [Project Milestones](https://github.com/kkm-horikawa/wagtail-reusable-blocks/milestones) for detailed roadmap.

## Requirements

- Python 3.10+
- Django 4.2+
- Wagtail 5.0+

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.

## Inspiration

- [WordPress Gutenberg Synced Patterns](https://wordpress.org/documentation/article/reusable-blocks/)
- [Wagtail CRX Reusable Content](https://docs.coderedcorp.com/wagtail-crx/features/snippets/reusable_content.html)
- [React Slots and Composition](https://react.dev/learn/passing-props-to-a-component)
