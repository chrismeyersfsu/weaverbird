<template>
  <div class="widget-date-input">
    <div class="widget-date-input__container">
      <span class="widget-date-input__label">{{ label }}</span>
      <div class="widget-date-input__button" @click="openEditor">
        <i class="far fa-calendar" aria-hidden="true" />
      </div>
    </div>
    <popover class="widget-date-input__editor" :visible="isEditorOpened" :align="alignLeft" bottom>
      <div class="widget-date-input__editor-container">
        <CustomVariableList
          class="widget-date-input__editor-side"
          :availableVariables="availableVariables"
          :selectedVariables="selectedVariables"
          @selectCustomVariable="editCustomVariable"
          @input="selectVariable"
        />
        <div class="widget-date-input__editor-content" v-show="isCustom" ref="custom-editor">
          <Tabs
            class="widget-date-input__editor-header"
            :tabs="tabs"
            :selectedTab="selectedTab"
            @tabSelected="selectTab"
          />
          <div class="widget-date-input__editor-body">
            <Calendar v-if="isFixedTabSelected" v-model="currentTabValue" />
            <RelativeDateForm v-else v-model="currentTabValue" />
          </div>
          <div class="widget-date-input__editor-footer">
            <div
              class="widget-date-input__editor-button"
              ref="cancel"
              @click="closeEditor"
              v-text="'Cancel'"
            />
            <div
              class="widget-date-input__editor-button widget-date-input__editor-button--primary"
              ref="save"
              @click="saveCustomVariable"
              v-text="'Set date'"
            />
          </div>
        </div>
      </div>
    </popover>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator';

import Calendar from '@/components/Calendar.vue';
import { POPOVER_ALIGN } from '@/components/constants';
import Popover from '@/components/Popover.vue';
import Tabs from '@/components/Tabs.vue';
import { CustomDate, dateToString, relativeDateToString } from '@/lib/dates';
import {
  AvailableVariable,
  extractVariableIdentifier,
  VariableDelimiters,
  VariablesBucket,
} from '@/lib/variables';

import CustomVariableList from './CustomVariableList.vue';
import RelativeDateForm from './RelativeDateForm.vue';
/**
 * This component allow to select a variable or to switch between tabs and select a date on a Fixed (Calendar) or Dynamic way (RelativeDateForm),
 * each tab value is keeped in memory to avoid user to loose data when switching between tabs
 */
@Component({
  name: 'new-date-input',
  components: {
    CustomVariableList,
    Popover,
    Tabs,
    Calendar,
    RelativeDateForm,
  },
})
export default class NewDateInput extends Vue {
  @Prop({ default: '' })
  value!: string | CustomDate;

  @Prop({ default: () => [] })
  availableVariables!: VariablesBucket;

  @Prop({ default: () => ({ start: '', end: '' }) })
  variableDelimiters!: VariableDelimiters;

  isEditorOpened = false;
  isEditingCustomVariable = false; // force to expand custom part of editor
  alignLeft: string = POPOVER_ALIGN.LEFT;
  selectedTab = 'Dynamic';

  get tabs(): string[] {
    return ['Dynamic', 'Fixed'];
  }

  // keep each tab value in memory to enable to switch between tabs without loosing content
  tabsValues: Record<string, CustomDate> = {
    Fixed: new Date(),
    Dynamic: { quantity: -1, duration: 'year' },
  };

  get currentTabValue(): CustomDate {
    return this.tabsValues[this.selectedTab];
  }

  set currentTabValue(value: CustomDate) {
    this.tabsValues[this.selectedTab] = value;
  }

  get variable(): AvailableVariable | undefined {
    if (typeof this.value !== 'string') return undefined;
    const identifier = extractVariableIdentifier(this.value, this.variableDelimiters);
    return this.availableVariables.find(v => v.identifier === identifier);
  }

  get selectedVariables(): string {
    // needed to select the custom button in CustomVariableList
    if (this.isCustom) {
      return 'custom';
    } else {
      return this.variable?.identifier ?? '';
    }
  }

  get hasCustomValue(): boolean {
    // value is custom if not undefined and not a preset variable
    return (this.value && !this.variable) as boolean;
  }

  get isCustom(): boolean {
    return this.hasCustomValue || this.isEditingCustomVariable;
  }

  get isFixedTabSelected(): boolean {
    return this.selectedTab === 'Fixed';
  }

  get label(): string {
    if (this.variable) {
      return this.variable.label;
    } else if (this.value instanceof Date) {
      return dateToString(this.value);
    } else if (this.value instanceof Object) {
      return relativeDateToString(this.value);
    } else {
      return 'Select a date';
    }
  }

  created() {
    this.initTabs();
  }

  // init tabs by selecting correct tab and value based on prop value
  initTabs(): void {
    if (this.value instanceof Date) {
      this.tabsValues.Fixed = this.value;
      this.selectTab('Fixed');
    } else if (this.value && typeof this.value !== 'string') {
      this.tabsValues.Dynamic = this.value;
      this.selectTab('Dynamic');
    }
  }

  openEditor(): void {
    this.isEditorOpened = true;
  }

  closeEditor(): void {
    this.isEditorOpened = false;
    this.isEditingCustomVariable = false;
  }

  selectVariable(value: string): void {
    const variableWithDelimiters = `${this.variableDelimiters.start}${value}${this.variableDelimiters.end}`;
    this.$emit('input', variableWithDelimiters);
    this.closeEditor();
  }

  editCustomVariable(): void {
    this.isEditingCustomVariable = true;
  }

  saveCustomVariable(): void {
    this.$emit('input', this.currentTabValue);
    this.closeEditor();
  }

  selectTab(tab: string): void {
    this.selectedTab = tab;
  }
}
</script>

<style scoped lang="scss">
@import '../../../../styles/variables';

$grey: #808080;
$grey-light: #d9d9d9;
$grey-extra-light: #f6f6f6;
$active-color-dark: #16406a;

.widget-date-input {
  max-width: 400px;
  position: relative;
}
.widget-date-input__container {
  border: 1px solid $grey-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.widget-date-input__label {
  padding: 10px 15px;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Montserrat', sans-serif;
  max-width: 100%;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.widget-date-input__button {
  padding: 10px 15px;
  background: $grey-extra-light;
  color: $grey;
  cursor: pointer;
}

.widget-date-input__container:hover {
  border-color: $active-color;
  .widget-date-input__button {
    background-color: $active-color-faded-2;
    color: $active-color;
  }
}

.widget-date-input__editor {
  margin-left: -5px;
  margin-right: -5px;
  background-color: #fff;
  box-shadow: 0 2px 10px 0 rgba(0, 0, 0, 0.25);
}
.widget-date-input__editor-container {
  display: flex;
  overflow: hidden;
  width: 100%;
  height: 100%;
}
.widget-date-input__editor-side {
  width: 200px;
  min-width: 200px;
  height: 100%;
  max-height: 380px;
  flex: 1 200px;
  overflow-x: hidden;
  overflow-y: auto;
}
.widget-date-input__editor-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1 100%;
  border-left: 1px solid #eeedf0;
}
.widget-date-input__editor-header {
  flex: 0;
  .tabs {
    margin-bottom: -1px;
  }
}
.widget-date-input__editor-body {
  flex: 1;
  height: 280px;
  min-height: 280px;
  width: 280px;
  .vc-container {
    border: none;
    margin: 1px;
    width: 100%;
  }
  .widget-relative-date-form {
    margin: 20px;
  }
}
.widget-date-input__editor-footer {
  flex: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-top: 1px solid #eeedf0;
  padding: 15px 20px;
}
.widget-date-input__editor-button {
  @extend %button-default;
  min-width: 100px;
  flex: 1;
  background: $grey-extra-light;
  color: $base-color;
  text-align: center;
  &:hover {
    background: $grey-light;
  }
  + .widget-date-input__editor-button {
    margin-left: 15px;
  }
}
.widget-date-input__editor-button--primary {
  background: $active-color;
  color: white;
  &:hover {
    background: $active-color-dark;
  }
}
</style>
