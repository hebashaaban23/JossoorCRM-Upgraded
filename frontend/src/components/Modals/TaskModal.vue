<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Task') : __('Create Task') }}
        </h3>
        <Button
          v-if="task?.reference_docname"
          size="sm"
          :label="task.reference_doctype == 'CRM Deal' ? __('Open Deal') : __('Open Lead')"
          :iconRight="ArrowUpRightIcon"
          @click="redirect()"
        />
      </div>
    </template>

    <template #body-content>
      <div class="flex flex-col gap-5">

        <!-- Task Type -->
        <div class="space-y-1.5">
          <div class="text-xs font-medium text-ink-gray-5">{{ __('Task Type') }} <span class="text-red-500">*</span></div>
          <Dropdown :options="taskTypeOptions(updateTaskType)" class="w-full">
            <Button
              :label="typeLabel(_task.task_type) || __('Select task type...')"
              class="w-full justify-between rounded-lg border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-8 hover:bg-surface-gray-3"
            >
              <template #suffix>
                
              </template>
            </Button>
          </Dropdown>
        </div>

        <!-- Meeting Attendees -->
        <div v-if="showAttendees" class="space-y-1.5">
          <div class="text-xs font-medium text-ink-gray-5">{{ __('Attendees') }}</div>
          <Autocomplete
            :key="_task.task_type"
            :options="userOptions"
            v-model="selectedUsers"
            :placeholder="__('Search and add attendees...')"
            :multiple="true"
            :compareFn="(a, b) => a?.value === b?.value"
          >
            <template #item-prefix="{ option }">
              <img v-if="option.image" :src="option.image" class="mr-2 h-6 w-6 rounded-full" />
            </template>
          </Autocomplete>
        </div>

        <!-- Description -->
        <div class="space-y-1.5">
          <div class="text-xs font-medium text-ink-gray-5">{{ __('Description') }}</div>
          <TextEditor
            variant="outline"
            ref="description"
            editor-class="!prose-sm overflow-auto min-h-[140px] max-h-64 py-2 px-3 rounded-lg border border-outline-gray-2 bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_task.description"
            @change="(val) => (_task.description = val)"
            :placeholder="__('Add a description...')"
          />
        </div>

        <!-- Row: Assignee + Status -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <div class="text-xs font-medium text-ink-gray-5">{{ __('Assigned To') }}</div>
            <Link
              class="form-control w-full"
              :value="getUser(_task.assigned_to)?.full_name"
              doctype="User"
              @change="(option) => (_task.assigned_to = option)"
              :placeholder="__('Select assignee...')"
              :filters="{ name: ['in', crmUserNames] }"
              :hideMe="true"
            >
              <template #prefix>
                <UserAvatar class="mr-2 !h-4 !w-4" :user="_task.assigned_to" />
              </template>
              <template #item-prefix="{ option }">
                <UserAvatar class="mr-2" :user="option.value" size="sm" />
              </template>
              <template #item-label="{ option }">
                <Tooltip :text="option.value">
                  <div class="cursor-pointer text-ink-gray-9">
                    {{ getUser(option.value)?.full_name }}
                  </div>
                </Tooltip>
              </template>
            </Link>
          </div>

          <div class="space-y-1.5">
            <div class="text-xs font-medium text-ink-gray-5">{{ __('Status') }}</div>
            <Dropdown :options="taskStatusOptions(updateTaskStatus)" class="w-full">
              <Button :label="_task.status" class="w-full justify-between">
                <template #prefix>
                  <TaskStatusIcon :status="_task.status" class="mr-2" />
                </template>
              </Button>
            </Dropdown>
          </div>
        </div>

        <!-- Row: Due Date + Reminder -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <div class="text-xs font-medium text-ink-gray-5">{{ __('Due Date') }}</div>
            <DateTimePicker
              class="datepicker w-full"
              v-model="_task.due_date"
              :placeholder="__('Select due date...')"
              :formatter="(date) => getFormat(date, '', true, true)"
              input-class="border border-outline-gray-2 rounded-lg bg-surface-gray-2 w-full"
            />
          </div>

          <div class="space-y-1.5">
            <div class="text-xs font-medium text-ink-gray-5">{{ __('Reminder') }}</div>
            <DateTimePicker
              class="datepicker w-full"
              v-model="reminderAt"
              :placeholder="__('Set reminder (optional)...')"
              :formatter="(date) => getFormat(date, '', true, true)"
              input-class="border border-outline-gray-2 rounded-lg bg-surface-gray-2 w-full"
            />
            <div v-if="reminderError" class="text-xs text-red-500">{{ reminderError }}</div>
          </div>
        </div>

        <!-- Priority -->
        <div class="space-y-1.5">
          <div class="text-xs font-medium text-ink-gray-5">{{ __('Priority') }}</div>
          <Dropdown :options="taskPriorityOptions(updateTaskPriority)" class="w-full">
            <Button :label="_task.priority" class="w-full justify-between">
              <template #prefix>
                <TaskPriorityIcon :priority="_task.priority" class="mr-2" />
              </template>
            </Button>
          </Dropdown>
        </div>

        <ErrorMessage v-if="error" :message="__(error)" />

        <!-- Submit -->
        <div class="pt-1">
          <Button
            variant="solid"
            :label="editMode ? __('Update Task') : __('Save Task')"
            :loading="submitting"
            :disabled="submitting"
            class="w-full"
            @click="handleSubmit"
          />
        </div>

      </div>
    </template>
  </Dialog>
</template>

<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'

import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { taskStatusOptions, taskPriorityOptions, getFormat } from '@/utils'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import {
  TextEditor, Dropdown, Tooltip, call, DateTimePicker, Dialog, Button,
  Autocomplete, toast,
} from 'frappe-ui'
import { ref, watch, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

// ─── props / emits ────────────────────────────────────────────────────────────
const props = defineProps({
  task:    { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  doc:     { type: String, default: '' },
})
const show  = defineModel()
const tasks = defineModel('reloadTasks')
const emit  = defineEmits(['updateTask', 'after'])

// ─── stores / router ─────────────────────────────────────────────────────────
const router = useRouter()
const { users, getUser } = usersStore()

// ─── state ────────────────────────────────────────────────────────────────────
const submitting    = ref(false)
const bootstrapping = ref(false)
const editMode      = ref(false)
const error         = ref('')
const reminderAt    = ref(null)
const reminderError = ref('')
const selectedUsers = ref([])
const description   = ref(null)
const title         = ref(null)

const _task = ref({
  title: '', description: '', assigned_to: '', due_date: '',
  status: 'Backlog', priority: 'Low',
  reference_doctype: props.doctype, reference_docname: null,
  task_type: '', meeting_attendees: [],
})

// ─── computed ─────────────────────────────────────────────────────────────────
const showAttendees = computed(() => _task.value.task_type === 'team meeting')

const userOptions = computed(() => {
  const list = users?.data?.crmUsers
  if (!Array.isArray(list)) return []
  return list.map(u => ({ label: u.full_name || u.name, value: u.name, image: u.user_image }))
})

const crmUserNames = computed(() => {
  const list = users?.data?.crmUsers
  if (!Array.isArray(list)) return []
  return list.map(u => u.name)
})

// ─── helpers ──────────────────────────────────────────────────────────────────
const typeLabel = (v) => ({ call: __('Call'), 'team meeting': __('Meeting'), 'property showing': __('Property Showing') }[v] || v)

function taskTypeOptions(cb) {
  return [
    { label: __('Call'),             value: 'call',             onClick: () => cb('call') },
    { label: __('Meeting'),          value: 'team meeting',     onClick: () => cb('team meeting') },
    { label: __('Property Showing'), value: 'property showing', onClick: () => cb('property showing') },
  ]
}
function updateTaskType(value) {
  _task.value.task_type = value
  _task.value.title = typeLabel(value)
  if (value !== 'team meeting') { _task.value.meeting_attendees = []; selectedUsers.value = [] }
}
function updateTaskStatus(s)   { _task.value.status   = s }
function updateTaskPriority(p) { _task.value.priority = p }

function selectedToChild(arr) {
  if (!Array.isArray(arr)) return []
  return arr.map(opt => ({ user: opt?.value ?? opt }))
}
function attendeesToSelected(arr) {
  if (!Array.isArray(arr) || !arr.length) return []
  const ids = arr.map(a => a.user || a.crm_task_user)
  return userOptions.value.filter(opt => ids.includes(opt.value))
}

function redirect() {
  if (!props.task?.reference_docname) return
  const name   = props.task.reference_doctype === 'CRM Deal' ? 'Deal' : 'Lead'
  const params = name === 'Deal' ? { dealId: props.task.reference_docname } : { leadId: props.task.reference_docname }
  router.push({ name, params })
}

function normalizeDatetime(val) {
  if (!val) return null
  return typeof val === 'string' ? val : getFormat(val, 'YYYY-MM-DD HH:mm:ss')
}

function validateReminder() {
  if (!reminderAt.value) return true
  const d = typeof reminderAt.value === 'string' ? new Date(reminderAt.value) : reminderAt.value
  if (d <= new Date()) {
    reminderError.value = __('Reminder must be a future date and time')
    return false
  }
  reminderError.value = ''
  return true
}

// ─── reminder helpers ─────────────────────────────────────────────────────────
async function insertReminder(taskName, assignedTo) {
  if (!reminderAt.value || !taskName) return
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: 'Reminder',
        user: assignedTo || getUser()?.name,
        remind_at: normalizeDatetime(reminderAt.value),
        description: _task.value.title,
        reference_doctype: 'CRM Task',
        reference_docname: taskName,
      },
    })
  } catch (e) { console.warn('Reminder insert failed', e) }
}

async function upsertReminder(taskName, assignedTo) {
  if (!reminderAt.value || !taskName) return
  try {
    const list = await call('frappe.client.get_list', {
      doctype: 'Reminder',
      filters: { reference_doctype: 'CRM Task', reference_docname: taskName },
      fields: ['name'], limit: 1,
    })
    if (list?.length) {
      await call('frappe.client.set_value', {
        doctype: 'Reminder', name: list[0].name,
        fieldname: { remind_at: normalizeDatetime(reminderAt.value) },
      })
    } else {
      await insertReminder(taskName, assignedTo)
    }
  } catch (e) { console.warn('Reminder upsert failed', e) }
}

// ─── submit ───────────────────────────────────────────────────────────────────
async function handleSubmit() {
  if (submitting.value) return

  // Task type validation
  if (!_task.value.task_type) {
    toast.error(__('Task Type is required'))
    return
  }

  if (!validateReminder()) return

  error.value = ''
  submitting.value = true
  try {
    await doSave()
  } catch (e) {
    console.error('[TaskModal] save error:', e)
    error.value = e?.message || __('Something went wrong')
  } finally {
    submitting.value = false
  }
}

async function doSave() {
  if (!_task.value.assigned_to) {
    _task.value.assigned_to = getUser()?.name || ''
  }

  const isMeeting = _task.value.task_type === 'team meeting'

  /* ── EDIT ── */
  if (_task.value.name) {
    if (isMeeting) {
      const doc = await call('frappe.client.get', { doctype: 'CRM Task', name: _task.value.name })
      Object.assign(doc, {
        title: _task.value.title, description: _task.value.description,
        assigned_to: _task.value.assigned_to, due_date: _task.value.due_date,
        status: _task.value.status, priority: _task.value.priority,
        task_type: _task.value.task_type || null,
        meeting_attendees: selectedToChild(selectedUsers.value),
      })
      const saved = await call('frappe.client.save', { doc })
      await upsertReminder(saved?.name, saved?.assigned_to)
      tasks.value?.reload?.()
      emit('after', saved)
    } else {
      const d = await call('frappe.client.set_value', {
        doctype: 'CRM Task', name: _task.value.name,
        fieldname: {
          title: _task.value.title, description: _task.value.description,
          assigned_to: _task.value.assigned_to, due_date: _task.value.due_date,
          status: _task.value.status, priority: _task.value.priority,
          task_type: _task.value.task_type || null,
        },
      })
      await upsertReminder(d?.name, d?.assigned_to)
      tasks.value?.reload?.()
      emit('after', d)
    }
    show.value = false
    return
  }

  /* ── CREATE ── */
  let d
  try {
    d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Task',
        reference_doctype: props.doctype,
        reference_docname: props.doc || null,
        title: _task.value.title,
        description: _task.value.description,
        assigned_to: _task.value.assigned_to,
        due_date: _task.value.due_date,
        status: _task.value.status,
        priority: _task.value.priority,
        task_type: _task.value.task_type || null,
        ...(isMeeting ? { meeting_attendees: selectedToChild(selectedUsers.value) } : {}),
      },
    })
  } catch (err) {
    const msg = err?.message || err?.exc || ''
    throw new Error(
      msg.includes('MandatoryError') || msg.includes('mandatory')
        ? __('Title is mandatory')
        : msg || __('Failed to create task')
    )
  }

  // insert succeeded — close first, then do side-effects
  show.value = false
  await nextTick()

  const taskName = d?.name
  if (taskName) {
    await insertReminder(taskName, d?.assigned_to)
capture('task_created')
    tasks.value?.reload?.()
    emit('after', d, true)
    toast.success(__('Task created'))
  }
}

// ─── render (reset / load) ────────────────────────────────────────────────────
async function render() {
  if (bootstrapping.value) return
  error.value = ''
  reminderError.value = ''
  editMode.value = false
  bootstrapping.value = true

  // Auto-focus title field
  setTimeout(() => title.value?.el?.focus?.(), 100)

  try {
    if (!props.task?.name) {
      // CREATE mode — reset everything
      reminderAt.value = null
      selectedUsers.value = []
      _task.value = {
        title: '', description: '', assigned_to: '', due_date: '',
        status: 'Backlog', priority: 'Low',
        reference_doctype: props.doctype,
        reference_docname: props.doc || null,
        task_type: '', meeting_attendees: [],
      }
    } else {
      // EDIT mode — load full doc
      const full = await call('frappe.client.get', { doctype: 'CRM Task', name: props.task.name })
      _task.value = { ...full }
      editMode.value = true

      await nextTick()
      selectedUsers.value = attendeesToSelected(full.meeting_attendees || [])

      const reminders = await call('frappe.client.get_list', {
        doctype: 'Reminder',
        filters: { reference_doctype: 'CRM Task', reference_docname: props.task.name },
        fields: ['name', 'remind_at'], limit: 1,
      })
      reminderAt.value = reminders?.length ? reminders[0].remind_at : null
    }
  } finally {
    bootstrapping.value = false
  }
}

// ─── watchers ─────────────────────────────────────────────────────────────────
watch(selectedUsers, (arr) => {
  if (bootstrapping.value) return
  _task.value.meeting_attendees = selectedToChild(arr || [])
}, { immediate: false })

watch(show, (isOpen) => { if (isOpen) render() })
onMounted(() => { if (show.value) render() })
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>