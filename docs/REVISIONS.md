# Revisions & Workflows Guide

wagtail-reusable-blocks v0.3.0+ integrates with Wagtail's standard mixins for revision history, draft/publish workflow, locking, and approval workflows.

## Overview

ReusableBlock now inherits from the following Wagtail mixins:

- **RevisionMixin** - Track changes and restore previous versions
- **DraftStateMixin** - Save drafts before publishing
- **LockableMixin** - Prevent concurrent editing conflicts
- **WorkflowMixin** - Integration with Wagtail approval workflows
- **PreviewableMixin** - Live preview in admin

## Revision History

### Viewing Revisions

1. Go to **Snippets > Reusable Blocks**
2. Click on a block to edit
3. Click the **History** tab to see all revisions

### Restoring a Previous Version

1. In the History tab, find the revision you want to restore
2. Click **Preview** to see what it looked like
3. Click **Revert to this revision** to restore it

### Programmatic Access

```python
from wagtail_reusable_blocks.models import ReusableBlock

block = ReusableBlock.objects.get(slug='my-block')

# Get all revisions
revisions = block.revisions.all()

# Get the latest revision
latest = block.latest_revision

# Restore a specific revision
old_revision = block.revisions.get(id=123)
old_revision.publish()
```

## Draft/Publish Workflow

### Saving as Draft

1. Edit a ReusableBlock
2. Click **Save draft** instead of **Publish**
3. Changes are saved but not live on the site

### Publishing a Draft

1. Edit a block with unpublished changes
2. Review the changes
3. Click **Publish** to make them live

### Checking Draft Status

```python
block = ReusableBlock.objects.get(slug='my-block')

# Check if block is live (published)
print(block.live)  # True/False

# Check if there are unpublished changes
print(block.has_unpublished_changes)  # True/False
```

### Admin UI Indicators

- **Live** badge - Block is published and visible
- **Draft** badge - Block has unpublished changes
- **Live + Draft** - Published with pending changes

## Scheduled Publishing

### Schedule Go-Live

1. Edit a ReusableBlock
2. In the **Publishing schedule** section, set **Go-live date/time**
3. Save the block
4. Block will automatically publish at the scheduled time

### Schedule Expiry

1. Edit a ReusableBlock
2. Set **Expiry date/time**
3. Block will automatically unpublish at the scheduled time

### Programmatic Scheduling

```python
from django.utils import timezone
from datetime import timedelta

block = ReusableBlock.objects.get(slug='my-block')

# Schedule to go live tomorrow
block.go_live_at = timezone.now() + timedelta(days=1)
block.save()

# Schedule to expire in a week
block.expire_at = timezone.now() + timedelta(weeks=1)
block.save()
```

## Locking

### Locking a Block

1. Edit a ReusableBlock
2. Click **Lock** in the actions menu
3. Other users cannot edit while locked

### Unlocking

1. Click **Unlock** to allow editing by others
2. Admins can unlock blocks locked by other users

### Checking Lock Status

```python
block = ReusableBlock.objects.get(slug='my-block')

# Check if locked
print(block.locked)  # True/False

# Check who locked it
print(block.locked_by)  # User object or None

# Check when it was locked
print(block.locked_at)  # datetime or None
```

## Approval Workflows

### Setting Up a Workflow

1. Go to **Settings > Workflows** in Wagtail admin
2. Create a new workflow or use an existing one
3. The workflow will apply to ReusableBlock snippets

### Submitting for Approval

1. Edit a ReusableBlock
2. Click **Submit for moderation**
3. Approvers will be notified

### Approving/Rejecting

1. Approvers see pending items in their dashboard
2. Review the changes
3. Click **Approve** or **Request changes**

### Workflow States

```python
block = ReusableBlock.objects.get(slug='my-block')

# Get current workflow state
workflow_state = block.current_workflow_state

if workflow_state:
    print(f"Status: {workflow_state.status}")
    print(f"Workflow: {workflow_state.workflow}")
```

## Preview

### Live Preview

1. Edit a ReusableBlock
2. Click **Preview** to see how it will render
3. Changes are shown in real-time as you edit

### Custom Preview Template

```python
# settings.py
WAGTAIL_REUSABLE_BLOCKS = {
    'TEMPLATE': 'my_app/custom_preview.html',
}
```

## Best Practices

### When to Use Drafts

- Making significant content changes
- Collaborative editing with review needed
- Preparing updates for future publication

### When to Use Locking

- During active editing sessions
- For critical content that shouldn't be modified
- When coordinating with team members

### Workflow Recommendations

- Use simple approval for small teams
- Use multi-stage approval for enterprise content
- Consider automatic publishing for trusted editors

## Migration from v0.2.0

Existing blocks will automatically have:
- `live = True` (all existing blocks are live)
- `has_unpublished_changes = False`
- No revisions (history starts from v0.3.0)

To create initial revisions for existing blocks:

```python
from wagtail_reusable_blocks.models import ReusableBlock

for block in ReusableBlock.objects.all():
    block.save_revision()
```
