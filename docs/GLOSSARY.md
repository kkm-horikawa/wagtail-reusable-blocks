# Glossary

Key terminology used in this project. Reference this when you're unsure about naming or concepts.

## Core Concepts

### ReusableBlock

The main model that stores reusable content.

```python
class ReusableBlock(models.Model):
    name = models.CharField(...)       # "Summer Sale Banner"
    slug = models.SlugField(...)       # "summer-sale-banner"
    content = StreamField(...)         # The actual content
```

**Analogy**: Like a "master slide" in PowerPoint - edit once, updates everywhere.

### ReusableBlockChooserBlock

A StreamField block that lets editors select a ReusableBlock.

```python
body = StreamField([
    ('reusable', ReusableBlockChooserBlock()),  # ← This
])
```

**What it does**: Renders the selected ReusableBlock's content inline.

### Slot (v0.2.0+)

A named placeholder within a ReusableBlock where content can be injected.

```
┌─────────────────────────────────┐
│  ReusableBlock: "Card Template" │
│  ┌───────────────────────────┐  │
│  │ [slot:header]             │  │  ← Slot
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ [slot:body]               │  │  ← Slot
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**Analogy**: Like React's `{props.children}` or Vue's `<slot>`.

### SlotPlaceholderBlock (v0.2.0+)

A StreamField block used **inside** a ReusableBlock to mark where content can be injected.

```python
# Inside ReusableBlock.content
SlotPlaceholderBlock(
    slot_id="header",
    label="Header Content",
    default_content=[...]
)
```

### SlotFillBlock (v0.2.0+)

A StreamField block used **in pages** to inject content into a slot.

```python
# Inside Page.body
SlotFillBlock(
    target_slot="header",
    content=[RichTextBlock("My Header")]
)
```

### ReusableBlockWithSlotsBlock (v0.2.0+)

Extended version of ReusableBlockChooserBlock that shows slot editors.

```python
body = StreamField([
    ('reusable_with_slots', ReusableBlockWithSlotsBlock()),
])
```

## Wagtail Concepts (Background)

### Snippet

A Django model registered with Wagtail for admin editing, but not a Page.

```python
@register_snippet
class MySnippet(models.Model):
    ...
```

### StreamField

Wagtail's flexible content field that stores a sequence of blocks.

```python
body = StreamField([
    ('heading', HeadingBlock()),
    ('paragraph', RichTextBlock()),
])
```

### Block

A unit of content in StreamField. Can be simple (CharBlock) or complex (StructBlock).

### SnippetChooserBlock

Built-in Wagtail block for selecting a Snippet instance.

```python
StreamField([
    ('person', SnippetChooserBlock(Person)),
])
```

## Relationships

```
Wagtail Core                    This Package
───────────────────────────────────────────────────────────────
Snippet                    →    ReusableBlock (is a Snippet)
SnippetChooserBlock        →    ReusableBlockChooserBlock (extends)
(none)                     →    SlotPlaceholderBlock (new)
(none)                     →    SlotFillBlock (new)
(none)                     →    ReusableBlockWithSlotsBlock (new)
```

## Naming Conventions

### Models

| Name | Purpose |
|------|---------|
| `ReusableBlock` | Main snippet model |
| `ReusableBlockUsage` | Tracks where blocks are used (v0.3.0) |

### Blocks

| Name | Purpose |
|------|---------|
| `ReusableBlockChooserBlock` | Choose a ReusableBlock |
| `ReusableBlockWithSlotsBlock` | Choose + fill slots |
| `SlotPlaceholderBlock` | Define a slot in ReusableBlock |
| `SlotFillBlock` | Fill a slot in Page |

### Settings

```python
WAGTAIL_REUSABLE_BLOCKS = {
    'BLOCK_TYPES': [...],        # Allowed blocks in ReusableBlock.content
    'MAX_NESTING_DEPTH': 5,      # Prevent deep nesting
    'TRACK_USAGE': True,         # Enable usage tracking (v0.3.0)
}
```

## Common Patterns

### "Single Source of Truth"

One ReusableBlock instance used by many pages. Edit once, all pages update.

### "Template + Content" (Slots)

ReusableBlock = Template (structure)
SlotFill = Content (what goes in the structure)

Same template, different content per page.

### "Circular Reference"

Block A → Block B → Block A (infinite loop)

Detected and prevented at save time with clear error message.

## Abbreviations

| Abbrev | Full Name |
|--------|-----------|
| WRB | wagtail-reusable-blocks (this package) |
| CRX | Wagtail CRX (CodeRed Extensions) |
| MVP | Minimum Viable Product (v0.1.0) |

## Version History

| Version | Codename | Focus |
|---------|----------|-------|
| v0.1.0 | MVP | Basic reusable blocks |
| v0.2.0 | Slots | Slot-based templating |
| v0.3.0 | Polish | Performance, caching, usage tracking |
