/**
 * Slot Chooser Widget for ReusableLayoutBlock
 *
 * Dynamically populates slot_id dropdowns based on the selected layout.
 * Extends Wagtail's StructBlockDefinition to add custom slot selection behavior.
 */

class ReusableLayoutBlockDefinition extends window.wagtailStreamField.blocks.StructBlockDefinition {
    render(placeholder, prefix, initialState, initialError) {
        const block = super.render(placeholder, prefix, initialState, initialError);

        // Use prefix to find fields (Wagtail's official pattern)
        const layoutFieldId = prefix + '-layout';
        const slotContentFieldId = prefix + '-slot_content';

        // Initialize SlotChooserWidget
        new SlotChooserWidget(layoutFieldId, slotContentFieldId);

        return block;
    }
}

class SlotChooserWidget {
    constructor(layoutFieldId, slotContentFieldId) {
        this.layoutFieldId = layoutFieldId;
        this.slotContentFieldId = slotContentFieldId;
        this.slots = [];

        this.init();
    }

    init() {
        // SnippetChooser creates a hidden input with the actual value
        // The field ID points to the container, we need to find the hidden input
        const layoutField = document.querySelector(`input[name="${this.layoutFieldId}"]`);
        if (!layoutField) {
            return;
        }

        // Listen for layout changes
        layoutField.addEventListener('change', (e) => {
            this.onLayoutChange(e.target.value);
        });

        // If a layout is already selected, load its slots
        if (layoutField.value) {
            this.onLayoutChange(layoutField.value);
        }

        // Use MutationObserver to watch for SlotFill blocks being added
        // This handles when new SlotFill blocks are added to slot_content StreamField
        const observer = new MutationObserver((mutations) => {
            let shouldUpdate = false;

            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the added node contains slot_id input fields
                        const hasSlotIdField = node.querySelector &&
                            node.querySelector('input[name*="slot_id"]');

                        if (hasSlotIdField) {
                            shouldUpdate = true;
                            break;
                        }
                    }
                }
                if (shouldUpdate) break;
            }

            if (shouldUpdate) {
                // Wait for DOM to be fully rendered
                setTimeout(() => {
                    this.updateSlotFields();
                }, 100);
            }
        });

        // Observe the entire document for now
        // We could optimize this by finding the specific slot_content container
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Store observer reference for cleanup if needed
        this.observer = observer;
    }

    async onLayoutChange(blockId) {
        if (!blockId) {
            this.slots = [];
            this.updateSlotFields();
            return;
        }

        try {
            const response = await fetch(
                `/admin/reusable-blocks/blocks/${blockId}/slots/`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.slots = data.slots;
            this.updateSlotFields();
        } catch (error) {
            console.error('Failed to fetch slots:', error);
            // Fallback: allow manual input
            this.slots = [];
        }
    }

    updateSlotFields() {
        // Find all slot_id fields within slot_content
        let slotIdFields = document.querySelectorAll(
            `input[name*="${this.slotContentFieldId}"][name*="slot_id"]`
        );

        // If not found, try alternative selector
        if (slotIdFields.length === 0) {
            slotIdFields = document.querySelectorAll(
                `input[name^="${this.slotContentFieldId}"][name$="-slot_id"]`
            );
        }

        slotIdFields.forEach((field) => {
            this.convertToDropdown(field);
        });
    }

    convertToDropdown(inputField) {
        // If no slots detected, keep as text input
        if (this.slots.length === 0) {
            return;
        }

        // Check if already converted
        if (inputField.dataset.slotChooserConverted === 'true') {
            this.updateDropdownOptions(inputField);
            return;
        }

        // Save current value
        const currentValue = inputField.value;

        // Create select element
        const select = document.createElement('select');
        select.name = inputField.name;
        select.id = inputField.id;
        select.className = inputField.className;
        select.dataset.slotChooserConverted = 'true';

        // Add empty option
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '-- Select a slot --';
        select.appendChild(emptyOption);

        // Add slot options
        this.slots.forEach(slot => {
            const option = document.createElement('option');
            option.value = slot.id;
            option.textContent = slot.label;

            // Mark slots with default content
            if (slot.has_default) {
                option.textContent += ' (has default)';
            }

            if (slot.id === currentValue) {
                option.selected = true;
            }

            select.appendChild(option);
        });

        // Replace input with select
        inputField.parentNode.replaceChild(select, inputField);
    }

    updateDropdownOptions(selectField) {
        const currentValue = selectField.value;

        // Clear existing options
        selectField.innerHTML = '';

        // Add empty option
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '-- Select a slot --';
        selectField.appendChild(emptyOption);

        // Add new slot options
        this.slots.forEach(slot => {
            const option = document.createElement('option');
            option.value = slot.id;
            option.textContent = slot.label;

            if (slot.has_default) {
                option.textContent += ' (has default)';
            }

            if (slot.id === currentValue) {
                option.selected = true;
            }

            select.appendChild(option);
        });
    }
}

// Register with Wagtail's telepath system
window.telepath.register(
    'wagtail_reusable_blocks.blocks.ReusableLayoutBlock',
    ReusableLayoutBlockDefinition
);
