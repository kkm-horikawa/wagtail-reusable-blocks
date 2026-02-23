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

        // Match only direct slot_id fields for THIS instance,
        // preventing parent from matching nested child fields
        const escapedPrefix = this.slotContentFieldId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        this.directSlotPattern = new RegExp(`^${escapedPrefix}-\\d+-value-slot_id$`);

        this.init();
    }

    init() {
        const layoutField = document.querySelector(`input[name="${this.layoutFieldId}"]`);
        if (!layoutField) {
            return;
        }

        layoutField.addEventListener('change', (e) => {
            this.onLayoutChange(e.target.value);
        });

        if (layoutField.value) {
            this.onLayoutChange(layoutField.value);
        }

        // Scope the MutationObserver to the slot_content container when possible,
        // falling back to document.body for robustness
        let observeTarget = document.body;
        const layoutSection = layoutField.closest('[data-contentpath="layout"]');
        if (layoutSection && layoutSection.parentElement) {
            const slotContentSection = layoutSection.parentElement.querySelector(
                ':scope > [data-contentpath="slot_content"]'
            );
            if (slotContentSection) {
                observeTarget = slotContentSection;
            }
        }

        const observer = new MutationObserver((mutations) => {
            let shouldUpdate = false;

            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        const candidates = node.querySelectorAll
                            ? node.querySelectorAll('input[name$="-slot_id"]')
                            : [];
                        for (const input of candidates) {
                            if (this.directSlotPattern.test(input.name)) {
                                shouldUpdate = true;
                                break;
                            }
                        }
                    }
                    if (shouldUpdate) break;
                }
                if (shouldUpdate) break;
            }

            if (shouldUpdate) {
                setTimeout(() => {
                    this.updateSlotFields();
                }, 100);
            }
        });

        observer.observe(observeTarget, {
            childList: true,
            subtree: true
        });

        this.observer = observer;
    }

    async onLayoutChange(blockId) {
        if (!blockId) {
            this.slots = [];
            this.updateSlotFields();
            return;
        }

        try {
            if (!window.wagtailReusableBlocksConfig?.slotsUrlTemplate) {
                console.error('[wagtail-reusable-blocks] slotsUrlTemplate not found.');
                return;
            }
            const slotsUrl = window.wagtailReusableBlocksConfig.slotsUrlTemplate.replace('__BLOCK_ID__', blockId);
            const response = await fetch(slotsUrl);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.slots = data.slots;
            this.updateSlotFields();
        } catch (error) {
            console.error('Failed to fetch slots:', error);
            this.slots = [];
        }
    }

    updateSlotFields() {
        // Search both input and select elements (converted fields become <select>)
        const allFields = document.querySelectorAll(
            'input[name$="-slot_id"], select[name$="-slot_id"]'
        );
        const slotIdFields = Array.from(allFields).filter(
            f => this.directSlotPattern.test(f.name)
        );

        slotIdFields.forEach((field) => {
            this.convertToDropdown(field);
        });
    }

    convertToDropdown(inputField) {
        if (this.slots.length === 0) {
            return;
        }

        if (inputField.dataset.slotChooserConverted === 'true') {
            this.updateDropdownOptions(inputField);
            return;
        }

        const currentValue = inputField.value;

        const select = document.createElement('select');
        select.name = inputField.name;
        select.id = inputField.id;
        select.className = inputField.className;
        select.dataset.slotChooserConverted = 'true';

        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '-- Select a slot --';
        select.appendChild(emptyOption);

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

        inputField.parentNode.replaceChild(select, inputField);
    }

    updateDropdownOptions(selectField) {
        const currentValue = selectField.value;

        selectField.innerHTML = '';

        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '-- Select a slot --';
        selectField.appendChild(emptyOption);

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

            selectField.appendChild(option);
        });
    }
}

// Register with Wagtail's telepath system
window.telepath.register(
    'wagtail_reusable_blocks.blocks.ReusableLayoutBlock',
    ReusableLayoutBlockDefinition
);
