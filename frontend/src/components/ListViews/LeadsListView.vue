<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader class="sm:mx-5 mx-3" @columnWidthUpdated="emit('columnWidthUpdated')">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        :align="column.key === 'status' ? 'center' : column.align"
        :class="column.key === 'status' ? 'status-header' : ''"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4 transition-all hover:bg-gray-200"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="() => emit('applyLikeFilter')"
          aria-label="Like Filter"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>

    <ListRows :rows="rows" v-slot="{ idx, column, item, row }" doctype="CRM Lead" @click="handleRowClick">
      <div
        v-if="column.key === '_assign'"
        class="h-full w-full"
        :class="row.original_lead ? 'highlight-yellow' : ''"
      >
        <MultipleAvatar
          :avatars="item"
          size="sm"
          @click="(event) => emit('applyFilter', { event, idx, column, item, firstColumn: columns[0] })"
        />
      </div>

      <div
        v-else-if="column.key === 'last_comment'"
        class="h-full w-full"
        :class="row.original_lead ? 'highlight-yellow' : ''"
        @click.stop
        @mousedown.stop
        @mouseup.stop
        @dblclick.stop
      >
        <LeadCommentsQuick :leadName="row.name" />
      </div>

      <div
        v-else
        class="h-full w-full"
        :class="row.original_lead ? 'highlight-yellow' : ''"
      >
        <ListRowItem 
          :item="item" 
          :align="column.key === 'status' ? 'center' : column.align"
          :class="column.key === 'status' ? 'status-cell' : ''"
        >
          <template #prefix>
            <div v-if="column.key === 'status'"></div>
            <div v-else-if="column.key === 'lead_name'">
              <Avatar
                v-if="item?.label"
                class="flex items-center"
                :image="item.image"
                :label="item.image_label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'lead_owner'">
              <Avatar
                v-if="item?.full_name"
                class="flex items-center"
                :image="item.user_image"
                :label="item.full_name"
                size="sm"
              />
            </div>
          </template>

          <template #default="{ label }">
            <div v-if="column.key === 'lead_name'">
              <RouterLink
                class="font-medium text-gray-900 hover:text-blue-600 hover:underline transition-colors"
                :to="{
                  name: 'Lead',
                  params: { leadId: row.name },
                  query: { view: route.query.view, viewType: route.params.viewType },
                }"
                @click.stop
              >
                {{ item?.label || label }}
              </RouterLink>
            </div>

            <div
              v-else-if="column.key === 'mobile_no'"
              class="flex items-center justify-between gap-3 group"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="text-gray-700 truncate">
                  {{ typeof item === 'object' && item ? item.label : item }}
                </span>
              </div>

             <div class="flex items-center gap-1.5 shrink-0 opacity-100 transition-opacity">
                <Button
                  v-if="getMobile(row)"
                  variant="ghost"
                  class="!p-1.5 !h-7 !w-7 hover:bg-green-50 hover:text-green-600 transition-all rounded-full"
                  @click.stop="makeCall(getMobile(row))"
                  :title="__('Call')"
                  aria-label="Call"
                >
                  <PhoneIcon class="h-3.5 w-3.5" />
                </Button>

                <Button
                  v-if="getMobile(row)"
                  variant="ghost"
                  class="!p-1.5 !h-7 !w-7 hover:bg-blue-50 hover:text-blue-600 transition-all rounded-full"
                  @click.stop="sendSMS(getMobile(row))"
                  :title="__('Send SMS')"
                  aria-label="Send SMS"
                >
                  <FeatherIcon name="message-circle" class="h-3.5 w-3.5" />
                </Button>

                <Button
                  v-if="getMobile(row)"
                  variant="ghost"
                  class="!p-1.5 !h-7 !w-7 hover:bg-green-50 hover:text-green-600 transition-all rounded-full"
                  @click.stop="openWhatsApp(getMobile(row))"
                  :title="__('Open WhatsApp')"
                  aria-label="Open WhatsApp"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="h-3.5 w-3.5" aria-hidden="true">
                    <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
                  </svg>
                </Button>
              </div>
            </div>

            <div v-else-if="column.key === 'status'" class="flex justify-center items-center w-full">
              <div class="relative inline-block">
                <button
                  :ref="el => { if (el) statusButtonRefs.set(row.name, el) }"
                  @click.stop="toggleStatusDropdown(row.name)"
                  :class="['status-badge', getStatusClass(getCurrentStatus(item))]"
                  :disabled="isUpdatingStatus"
                  type="button"
                  aria-haspopup="true"
                  :aria-expanded="activeDropdown === row.name"
                >
                  <span class="status-badge-text">{{ getCurrentStatus(item) }}</span>
                  <svg 
                    class="status-badge-icon" 
                    :class="{ 'rotate-180': activeDropdown === row.name }"
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                <Teleport to="body">
                  <transition name="fade" mode="out-in">
                    <div
                      v-if="activeDropdown === row.name"
                      :ref="el => { if (el) statusDropdownRef = el }"
                      :style="dropdownPosition"
                      class="status-dropdown-menu"
                      role="menu"
                      @click.stop
                    >
                      <div class="status-dropdown-header">
                        <span class="text-xs font-semibold text-gray-700">Update Status</span>
                        <button
                          @click.stop="closeStatusDropdown"
                          class="text-gray-400 hover:text-gray-600 transition-colors rounded-full p-1 hover:bg-gray-100"
                          aria-label="Close"
                        >
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <div class="status-dropdown-list">
                        <button
                          v-for="status in availableStatuses"
                          :key="status.value"
                          @click.stop="updateStatus(row.name, status.value, item, row)"
                          :class="[
                            'status-dropdown-item',
                            getCurrentStatus(item) === status.label ? 'status-dropdown-item-active' : ''
                          ]"
                          role="menuitem"
                        >
                          <div :class="['status-indicator', getStatusClass(status.label)]"></div>
                          <span class="status-dropdown-item-text">{{ status.label }}</span>
                          <svg 
                            v-if="getCurrentStatus(item) === status.label"
                            class="w-4 h-4 text-blue-600 flex-shrink-0" 
                            fill="currentColor" 
                            viewBox="0 0 20 20"
                          >
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </transition>
                </Teleport>
              </div>
            </div>

            <div
              v-else-if="
                ['modified','creation','first_response_time','first_responded_on','response_by'].includes(column.key)
              "
              class="truncate text-sm text-gray-600"
              @click="(event) => emit('applyFilter', { event, idx, column, item, firstColumn: columns[0] })"
            >
              <Tooltip :text="item?.label">
                <div class="hover:text-gray-900 transition-colors">{{ item?.timeAgo }}</div>
              </Tooltip>
            </div>

            <div v-else-if="column.key === '_liked_by'">
              <Button
                variant="ghosted"
                class="transition-all"
                :class="isLiked(item) ? 'fill-red-500 hover:fill-red-600' : 'fill-gray-300 hover:fill-red-400'"
                @click.stop.prevent="() => emit('likeDoc', { name: row.name, liked: isLiked(item) })"
                aria-label="Like this document"
              >
                <HeartIcon class="h-4 w-4" />
              </Button>
            </div>

            <div v-else-if="column.key === 'sla_status'" class="truncate text-base">
              <Badge
                v-if="item?.value"
                :variant="'subtle'"
                :theme="item.color"
                size="md"
                :label="item.value"
                @click="(event) => emit('applyFilter', { event, idx, column, item, firstColumn: columns[0] })"
              />
            </div>

            <div v-else-if="column.type === 'Check'">
              <FormControl
                type="checkbox"
                :modelValue="item"
                :disabled="true"
                class="text-gray-600"
              />
            </div>

            <div
              v-else
              class="truncate text-sm text-gray-700 hover:text-gray-900 transition-colors"
              @click="(event) => emit('applyFilter', { event, idx, column, item, firstColumn: columns[0] })"
            >
              {{ label }}
            </div>
          </template>
        </ListRowItem>
      </div>
    </ListRows>

    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown :options="listBulkActionsRef?.bulkActions?.(selections, unselectAll) || []">
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>

  </ListView>

  <CustomListFooter
    v-if="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  
  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Lead" />
</template>

<script setup>
import LeadCommentsQuick from '@/components/LeadCommentsQuick.vue'
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import CustomListFooter from '@/components/CustomListFooter.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  Tooltip,
  Button,
  FormControl,
  Badge,
  Dropdown,
  FeatherIcon,
  call,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { statusesStore } from '@/stores/statuses'
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, Teleport } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const route = useRoute()
const pageLengthCount = defineModel()
const list = defineModel('list')

const isLikeFilterApplied = computed(() => {
  return list.value?.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()
const { statusOptions } = statusesStore()

const isUpdatingStatus = ref(false)
const activeDropdown = ref(null)
const statusButtonRefs = new Map()
const statusDropdownRef = ref(null)
const dropdownPosition = ref({})

const availableStatuses = computed(() => {
  return statusOptions('lead') || []
})

function getCurrentStatus(item) {
  if (!item) return ''
  return item.value || item.label || item || ''
}

async function toggleStatusDropdown(rowName) {
  if (isUpdatingStatus.value) return
  
  if (activeDropdown.value === rowName) {
    closeStatusDropdown()
    return
  }
  
  activeDropdown.value = rowName
  
  await nextTick()
  calculateDropdownPosition(rowName)
}

function calculateDropdownPosition(rowName) {
  const trigger = statusButtonRefs.get(rowName)
  if (!trigger) return
  
  const rect = trigger.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth
  const dropdownHeight = 400
  const dropdownWidth = 260
  const spaceBelow = viewportHeight - rect.bottom
  const spaceAbove = rect.top
  
  let top, left
  
  // Determine vertical position
  if (spaceBelow >= dropdownHeight || spaceBelow > spaceAbove) {
    top = rect.bottom + 8
  } else {
    top = rect.top - dropdownHeight - 8
  }
  
  // Center horizontally relative to trigger
  left = rect.left + (rect.width / 2)
  
  // Prevent horizontal overflow
  const halfDropdown = dropdownWidth / 2
  if (left - halfDropdown < 10) {
    left = halfDropdown + 10
  } else if (left + halfDropdown > viewportWidth - 10) {
    left = viewportWidth - halfDropdown - 10
  }
  
  dropdownPosition.value = {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    transform: 'translateX(-50%)',
    zIndex: 9999
  }
}

function closeStatusDropdown() {
  activeDropdown.value = null
  dropdownPosition.value = {}
}

function handleRowClick() {
  if (activeDropdown.value) {
    closeStatusDropdown()
  }
}

function handleEscKey(event) {
  if (event.key === 'Escape') {
    closeStatusDropdown()
  }
}

function handleClickOutside(event) {
  if (activeDropdown.value && statusDropdownRef.value) {
    const dropdown = statusDropdownRef.value
    const triggerButton = statusButtonRefs.get(activeDropdown.value)
    
    if (!dropdown.contains(event.target) && 
        (!triggerButton || !triggerButton.contains(event.target))) {
      closeStatusDropdown()
    }
  }
}

function handleScroll(event) {
  if (activeDropdown.value && statusDropdownRef.value) {
    // Don't close if scrolling inside the dropdown itself
    if (statusDropdownRef.value.contains(event.target)) {
      return
    }
    // Close if scrolling outside the dropdown
    closeStatusDropdown()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', handleScroll, true)
  window.addEventListener('resize', closeStatusDropdown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscKey)
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScroll, true)
  window.removeEventListener('resize', closeStatusDropdown)
  statusButtonRefs.clear()
})

function getStatusClass(status) {
  if (!status) return 'status-default'
  
  const statusLower = String(status).toLowerCase().replace(/\s+/g, '-')
  
  const statusMap = {
    'new': 'status-new',
    'contacted': 'status-contacted',
    'follow-up': 'status-follow-up',
    'follow-up-to-meeting': 'status-follow-up-to-meeting',
    'no-answer': 'status-no-answer',
    'meeting': 'status-meeting',
    'follow-up-after-meeting': 'status-follow-up-after-meeting',
    'not-interested': 'status-not-interested',
    'rotation': 'status-rotation',
    'low-budget': 'status-low-budget',
    'reservation': 'status-reservation',
    'done-deal': 'status-done-deal',
    'junk': 'status-junk',
    'qualified': 'status-qualified',
    'unqualified': 'status-unqualified',
  }
  
  return statusMap[statusLower] || 'status-default'
}

async function updateStatus(leadName, newStatus, currentItem, row) {
  if (!leadName || !newStatus) {
    console.warn('Missing leadName or newStatus')
    return
  }

  if (isUpdatingStatus.value) return

  const currentStatus = getCurrentStatus(currentItem)
  if (currentStatus === newStatus) {
    closeStatusDropdown()
    return
  }

  closeStatusDropdown()
  isUpdatingStatus.value = true

  try {
    const result = await call('frappe.client.set_value', {
      doctype: 'CRM Lead',
      name: leadName,
      fieldname: 'status',
      value: newStatus,
    })

    if (currentItem && typeof currentItem === 'object') {
      currentItem.value = newStatus
      currentItem.label = newStatus
    }

    if (row && row.status) {
      if (typeof row.status === 'object') {
        row.status.value = newStatus
        row.status.label = newStatus
      } else {
        row.status = newStatus
      }
    }

    if (window.frappe?.show_alert) {
      window.frappe.show_alert({
        message: `Status updated to "${newStatus}"`,
        indicator: 'green'
      }, 3)
    }

    if (list.value?.reload) {
      await list.value.reload()
    }
  } catch (error) {
    console.error('Failed to update status:', error)

    if (window.frappe?.show_alert) {
      window.frappe.show_alert({
        message: error.message || 'Failed to update status',
        indicator: 'red'
      }, 5)
    }

    if (list.value?.reload) {
      await list.value.reload()
    }
  } finally {
    isUpdatingStatus.value = false
  }
}

function isLiked(item) {
  if (!item) return false
  try {
    const likedByMe = JSON.parse(item)
    return Array.isArray(likedByMe) && likedByMe.includes(user)
  } catch {
    return false
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)
defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})

function getMobile(row) {
  const v = row?.mobile_no
  return typeof v === 'object' && v !== null ? v.label : v || ''
}

function makeCall(number) {
  const n = String(number || '').trim()
  if (n) window.open(`tel:${n}`)
}

function openWhatsApp(number) {
  const phone = String(number || '').replace(/\D/g, '')
  if (phone) window.open(`https://wa.me/${phone}`, '_blank')
}

function sendSMS(number) {
  if (!number) return

  const cleaned = String(number).replace(/\s+/g, '')
  const smsUrl = `sms:${encodeURIComponent(cleaned)}`

  try {
    window.location.href = smsUrl
  } catch (e) {
    console.warn('Failed to open SMS handler', e)
  }
}
</script>

<style scoped>
.highlight-yellow {
  background-color: #FFFEF9 !important;
  border-left: 3px solid #FCD34D;
}

/* Status header and cell centering */
.status-header {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.status-header :deep(*) {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.status-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

.status-cell :deep(*) {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

/* Status Badge (Button) */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 7px;
  border: 1px solid;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 120px;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  position: relative;
}

/* Responsive adjustments for status badge */
@media (max-width: 768px) {
  .status-badge {
    min-width: 120px;
    padding: 6px 12px;
    font-size: 12px;
  }
}

@media (max-width: 640px) {
  .status-badge {
    min-width: 100px;
    padding: 5px 10px;
    font-size: 11px;
  }
}

.status-badge:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.12);
}

.status-badge:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
}

.status-badge:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.status-badge-text {
  flex: 1;
  text-align: center;
  white-space: nowrap;
}

.status-badge-icon {
  width: 12px;
  height: 12px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

/* Dropdown Menu */
.status-dropdown-menu {
  position: fixed;
  min-width: 180px;
  max-width: 220px;
  background: white;
  border-radius: 12px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  animation: dropdown-appear 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Responsive dropdown */
@media (max-width: 640px) {
  .status-dropdown-menu {
    min-width: 200px;
    max-width: 240px;
    border-radius: 12px;
  }
}

@media (max-width: 480px) {
  .status-dropdown-menu {
    min-width: 180px;
    max-width: 220px;
    left: 50% !important;
    right: auto !important;
    transform: translateX(-50%) !important;
  }
}

@keyframes dropdown-appear {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.status-dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.status-dropdown-list {
  max-height: 240px;
  overflow-y: auto;
  padding: 6px;
}

/* Responsive dropdown list */
@media (max-width: 640px) {
  .status-dropdown-list {
    max-height: 300px;
    padding: 6px;
  }
}

@media (max-width: 480px) {
  .status-dropdown-list {
    max-height: 250px;
  }
}

.status-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  font-size: 12.5px;
  font-weight: 500;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: #374151;
}

/* Responsive dropdown items */
@media (max-width: 640px) {
  .status-dropdown-item {
    padding: 9px 12px;
    font-size: 13px;
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .status-dropdown-item {
    padding: 8px 10px;
    font-size: 12px;
  }
}

.status-dropdown-item:hover {
  background: #f3f4f6;
  transform: translateX(2px);
}

.status-dropdown-item-active {
  background: #eff6ff;
  color: #1e40af;
  font-weight: 600;
}

.status-dropdown-item-active:hover {
  background: #dbeafe;
}

.status-dropdown-item-text {
  flex: 1;
  white-space: nowrap;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid;
}

/* STATUS COLOR CLASSES */
.status-new {
  background-color: #dbeafe;
  color: #1e40af;
  border-color: #93c5fd;
}

.status-new .status-indicator {
  background-color: #3b82f6;
  border-color: #1e40af;
}

.status-contacted {
  background-color: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}

.status-contacted .status-indicator {
  background-color: #10b981;
  border-color: #065f46;
}

.status-follow-up {
  background-color: #ede9fe;
  color: #6b21a8;
  border-color: #c4b5fd;
}

.status-follow-up .status-indicator {
  background-color: #a855f7;
  border-color: #6b21a8;
}

.status-follow-up-to-meeting {
  background-color: #e0e7ff;
  color: #4338ca;
  border-color: #a5b4fc;
}

.status-follow-up-to-meeting .status-indicator {
  background-color: #6366f1;
  border-color: #4338ca;
}

.status-no-answer {
  background-color: #f3e8ff;
  color: #6b21a8;
  border-color: #d8b4fe;
}

.status-no-answer .status-indicator {
  background-color: #a855f7;
  border-color: #7c3aed;
}

.status-meeting {
  background-color: #cffafe;
  color: #0e7490;
  border-color: #67e8f9;
}

.status-meeting .status-indicator {
  background-color: #06b6d4;
  border-color: #0e7490;
}

.status-follow-up-after-meeting {
  background-color: #ccfbf1;
  color: #0f766e;
  border-color: #5eead4;
}

.status-follow-up-after-meeting .status-indicator {
  background-color: #14b8a6;
  border-color: #0f766e;
}

.status-not-interested {
  background-color: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.status-not-interested .status-indicator {
  background-color: #ef4444;
  border-color: #991b1b;
}

.status-rotation {
  background-color: #fed7aa;
  color: #c2410c;
  border-color: #fdba74;
}

.status-rotation .status-indicator {
  background-color: #f97316;
  border-color: #c2410c;
}

.status-junk {
  background-color: #fecaca;
  color: #991b1b;
  border-color: #f87171;
}

.status-junk .status-indicator {
  background-color: #dc2626;
  border-color: #991b1b;
}

.status-low-budget {
  background-color: #fef3c7;
  color: #92400e;
  border-color: #fde047;
}

.status-low-budget .status-indicator {
  background-color: #facc15;
  border-color: #92400e;
}

.status-reservation {
  background-color: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}

.status-reservation .status-indicator {
  background-color: #10b981;
  border-color: #065f46;
}

.status-done-deal {
  background-color: #bbf7d0;
  color: #166534;
  border-color: #4ade80;
}

.status-done-deal .status-indicator {
  background-color: #22c55e;
  border-color: #166534;
}

.status-qualified {
  background-color: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}

.status-qualified .status-indicator {
  background-color: #10b981;
  border-color: #065f46;
}

.status-unqualified {
  background-color: #f3f4f6;
  color: #4b5563;
  border-color: #d1d5db;
}

.status-unqualified .status-indicator {
  background-color: #9ca3af;
  border-color: #6b7280;
}

.status-default {
  background-color: #f3f4f6;
  color: #4b5563;
  border-color: #d1d5db;
}

.status-default .status-indicator {
  background-color: #9ca3af;
  border-color: #6b7280;
}

/* Scrollbar styling for dropdown */
.status-dropdown-list::-webkit-scrollbar {
  width: 8px;
}

.status-dropdown-list::-webkit-scrollbar-track {
  background: transparent;
  margin: 4px;
}

.status-dropdown-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.status-dropdown-list::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
  border: 2px solid transparent;
  background-clip: padding-box;
}
</style>