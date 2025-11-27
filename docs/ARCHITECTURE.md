# Architecture & Design Decisions

This document explains the architectural decisions and the "why" behind them. Read this when you return to the project after a long break.

## The Problem We're Solving

### Current Wagtail Limitations

1. **Snippets are too simple**: They store data but don't support full StreamField rendering in pages
2. **Page blocks are not reusable**: Copy/paste requires manual updates everywhere
3. **No single source of truth**: Same content duplicated across pages gets out of sync

### What Users Want

> "I want to create a promotional banner once, use it on 50 pages, and when I update it, all 50 pages update automatically."

## Core Architecture

### Phase 1: Reusable Blocks (v0.1.0)

```mermaid
flowchart TB
    subgraph Admin["Wagtail Admin"]
        subgraph Snippet["Snippets > Reusable Blocks"]
            RB["ReusableBlock: Promo Banner"]
            RB --> Name["name: Summer Sale Banner"]
            RB --> Slug["slug: summer-sale-banner"]
            RB --> Content["content: StreamField"]
            Content --> RT["RichTextBlock"]
            Content --> HTML["RawHTMLBlock"]
        end
    end

    subgraph PageEditor["Page Editor: HomePage"]
        Body["body: StreamField"]
        Body --> B1["RichTextBlock: Welcome"]
        Body --> Chooser["ReusableBlockChooserBlock"]
        Body --> B2["RichTextBlock: More content"]
        Chooser -.->|"selects"| RB
    end

    subgraph Rendered["Rendered Page"]
        R1["Welcome to our site"]
        R2["Summer Sale!"]
        R3["CTA content"]
        R4["More content..."]
    end

    Admin --> PageEditor
    PageEditor --> Rendered
```

**Key Decision: Use SnippetChooserBlock pattern**

- Wagtail already has `SnippetChooserBlock` for choosing snippets
- We extend this pattern with custom rendering logic
- Familiar to Wagtail developers

### Phase 2: Slot System (v0.2.0)

```mermaid
flowchart TB
    subgraph ReusableBlock["ReusableBlock: Two Column Layout"]
        direction TB
        C1["&lt;div class='row'&gt;"]
        subgraph Sidebar["Slot: sidebar"]
            S1["slot_id: sidebar"]
            S1D["default: Default sidebar..."]
        end
        subgraph Main["Slot: main"]
            M1["slot_id: main"]
            M1D["default: Default content..."]
        end
        C2["&lt;/div&gt;"]
    end

    subgraph Page["Page: ArticlePage"]
        direction TB
        RBWS["ReusableBlockWithSlotsBlock"]
        RBWS -->|"selects"| ReusableBlock
        subgraph SlotContent["slot_content"]
            SF1["SlotFill: sidebar"]
            SF1 --> Nav["NavigationBlock"]
            SF1 --> Ads["AdsBlock"]
            SF2["SlotFill: main"]
            SF2 --> Article["RichTextBlock: Article..."]
        end
    end

    subgraph Output["Rendered Output"]
        direction TB
        O1["&lt;div class='row'&gt;"]
        subgraph OSidebar["col-4"]
            ON["Navigation"]
            OA["Ads"]
        end
        subgraph OMain["col-8"]
            OArt["Article content"]
        end
        O2["&lt;/div&gt;"]
    end

    ReusableBlock --> Output
    SlotContent -->|"injects into"| Output
```

**Slot Concept Visualization**

```mermaid
graph LR
    subgraph Template["ReusableBlock = Template"]
        T1["Header Area"]
        T2["[SLOT: sidebar]"]
        T3["[SLOT: main]"]
        T4["Footer Area"]
    end

    subgraph Content["Page = Content"]
        C1["SlotFill: sidebar<br/>→ Navigation, Ads"]
        C2["SlotFill: main<br/>→ Article Text"]
    end

    subgraph Result["Rendered Result"]
        R1["Header Area"]
        R2["Navigation + Ads"]
        R3["Article Text"]
        R4["Footer Area"]
    end

    T2 -.->|"filled by"| C1
    T3 -.->|"filled by"| C2
    Template --> Result
    Content --> Result
```

**Key Decision: Slots are StreamField blocks, not template tags**

Why not Django template tags?
- Template tags require code deployment
- Our goal is **no-deploy content changes**
- StreamField blocks can be managed in admin

**Key Decision: Store slot content in the page, not in the ReusableBlock**

- ReusableBlock defines the structure (template)
- Page defines the content for each slot
- This allows same layout with different content per page

## Data Flow

### Rendering a ReusableBlock with Slots

```mermaid
flowchart TD
    A["Page.body renders"] --> B["Encounters ReusableBlockWithSlotsBlock"]
    B --> C["Load ReusableBlock from DB"]
    C --> D["Parse content for SlotPlaceholderBlocks"]
    D --> E{"For each Slot"}
    E --> F{"Matching SlotFill exists?"}
    F -->|"Yes"| G["Render SlotFill.content"]
    F -->|"No"| H["Render default_content"]
    G --> I["Combine all rendered parts"]
    H --> I
    I --> J["Return complete HTML"]
```

### Circular Reference Detection

```mermaid
flowchart TD
    A["Save ReusableBlock"] --> B["Scan content for references"]
    B --> C{"References other ReusableBlock?"}
    C -->|"No"| D["Safe to save"]
    C -->|"Yes"| E["Add to visited set"]
    E --> F{"Already in visited?"}
    F -->|"Yes"| G["ERROR: Circular reference detected"]
    F -->|"No"| H["Recursively check referenced block"]
    H --> C
    D --> I["Save successful"]
    G --> J["Show error with reference chain"]
```

**Key Decision: Detect at save time, not render time**

- Fail fast: catch errors when editor saves
- Better UX: clear error message with reference chain
- Performance: no runtime overhead

## Model Relationships

```mermaid
erDiagram
    ReusableBlock {
        int id PK
        string name
        string slug UK
        json content
        datetime created_at
        datetime updated_at
    }

    Page {
        int id PK
        string title
        json body
    }

    ReusableBlockUsage {
        int id PK
        int block_id FK
        int page_id FK
        string field_name
        string block_path
    }

    ReusableBlock ||--o{ ReusableBlockUsage : "tracked by"
    Page ||--o{ ReusableBlockUsage : "uses"
```

## Why Not Use Existing Solutions?

| Solution | Problem |
|----------|---------|
| **Wagtail CRX** | Full framework, too heavy for simple use case |
| **Snippets + SnippetChooserBlock** | Doesn't render StreamField content inline |
| **Django Template Includes** | Requires code deployment, no admin UI |

## Configuration Philosophy

**Principle: Sensible defaults, full customization**

```python
# Minimal setup - works out of the box
INSTALLED_APPS = ['wagtail_reusable_blocks']

# Full customization available
WAGTAIL_REUSABLE_BLOCKS = {
    'BLOCK_TYPES': [...],      # Custom block types
    'CACHE_ENABLED': True,     # Performance
    'MAX_NESTING_DEPTH': 5,    # Safety limit
}
```

## Performance Strategy

```mermaid
flowchart LR
    subgraph v010["v0.1.0"]
        P1["1 query per block"]
        P1 --> P1R["Simple, acceptable"]
    end

    subgraph v030["v0.3.0"]
        P2["Caching layer"]
        P3["Bulk queries"]
        P4["Usage tracking"]
        P2 --> P2R["Render once, cache"]
        P3 --> P3R["Single query for all"]
        P4 --> P4R["Smart invalidation"]
    end
```

## Future Considerations (Not in Scope)

These are intentionally **not** planned:

1. **Visual slot editor**: Complex UI, high maintenance
2. **Real-time collaboration**: Wagtail doesn't support this natively
3. **A/B testing**: Should be separate package
4. **Multi-site**: Adds complexity, can be added later

## Questions This Document Should Answer

When you return to this project, you should be able to answer:

| Question | Answer |
|----------|--------|
| Why did we build this? | Reusable content with single source of truth |
| Why not use Wagtail CRX? | Too heavy, we need lightweight package |
| Why slots? | Enable layout templates without code deployment |
| Why detect circular refs at save time? | Better UX, fail fast |
| Why store slot content in page? | Same layout, different content per page |
