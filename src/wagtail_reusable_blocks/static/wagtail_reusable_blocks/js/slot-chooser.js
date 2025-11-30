/**
 * Slot Chooser Widget for ReusableLayoutBlock
 *
 * Dynamically populates slot_id dropdowns based on the selected layout.
 */

class SlotChooserWidget {
    constructor(layoutFieldId, slotContentFieldId) {
        this.layoutFieldId = layoutFieldId;
        this.slotContentFieldId = slotContentFieldId;
        this.slots = [];

        this.init();
    }

    init() {
        // Find the layout chooser field
        const layoutField = document.getElementById(this.layoutFieldId);
        if (!layoutField) {
            console.warn(`Layout field ${this.layoutFieldId} not found`);
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
        const slotIdFields = document.querySelectorAll(
            `[id^="${this.slotContentFieldId}"] input[name$="slot_id"]`
        );

        slotIdFields.forEach(field => {
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

// Export for use in Wagtail admin
window.SlotChooserWidget = SlotChooserWidget;
