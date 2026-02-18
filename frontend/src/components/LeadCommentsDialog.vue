<script setup>
import { ref, watch } from 'vue'
import { Dialog, Button, Textarea, Spinner, Avatar, call, toast } from 'frappe-ui'

const props = defineProps({
  show: { type: Boolean, default: false },
  doctype: { type: String, default: 'CRM Lead' },
  name: { type: String, required: true },     // docname
  pageSize: { type: Number, default: 20 },
  // لو فتحناه بهدف تعديل تعليق معيّن
  editComment: { type: Object, default: null }, // { name, content }
})
const emit = defineEmits(['update:show'])

const loading = ref(false)
const sending = ref(false)
const savingEdit = ref(false)
const error = ref('')
const comments = ref([])
const cursor = ref(null)

const newContent = ref('')
const newTitle = ref('') // Title for new feedback
const newType = ref('') // Default to empty for placeholder
const editing = ref(null) // {name, content, subject, comment_type}
import { FEEDBACK_TYPES } from '@/constants/feedbackTypes'

const typeOptions = FEEDBACK_TYPES


/** خيارات الريمايندر */
const addReminder = ref(false)
const reminderDatetime = ref('')
const reminderError = ref('')

function stripHtml (html='') {
  return String(html)
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
}

function isDelayedFlag(comment) {
  const flag = comment?.delayed
  return flag === 1 || flag === true || flag === '1' || flag === 'Yes'
}

watch(() => props.show, async (open) => {
  if (!open) return
  editing.value = props.editComment
    ? { name: props.editComment.name, content: stripHtml(props.editComment.content) }
    : null
  editing.value = props.editComment
    ? { name: props.editComment.name, content: stripHtml(props.editComment.content) }
    : null
  addReminder.value = false
  reminderDatetime.value = ''
  reminderError.value = ''
  await resetAndLoad()
})

async function refreshDelayedState() {
  try {
    await call('crm.api.reminders.recalc_delayed_for_doc', {
      doctype: props.doctype,
      name: props.name,
    })
  } catch (e) {
    console.debug('recalc_delayed_for_doc failed', e)
  }
}

async function resetAndLoad() {
  comments.value = []
  cursor.value = null
  error.value = ''
  await refreshDelayedState()
  await fetchComments()
}

async function fetchComments() {
  loading.value = true
  try {
    const filters = [
      ['Comment','reference_doctype','=',props.doctype],
      ['Comment','reference_name','=',props.name],
      ['Comment','comment_type','=','Comment'],
    ]
    if (cursor.value) filters.push(['Comment','creation','<',cursor.value])

    const res = await call('frappe.client.get_list', {
      doctype: 'Comment',
      fields: ['name','comment_by','owner','subject','content','creation','delayed'],
      filters,
      order_by: 'creation desc',
      limit_page_length: props.pageSize,
    })
    const items = Array.isArray(res?.message) ? res.message : (Array.isArray(res) ? res : [])
    comments.value.push(...items)
    if (items.length) cursor.value = items[items.length-1].creation
  } catch (e) {
    error.value = e?.message || 'Failed to load FeedBacks'
  } finally {
    loading.value = false
  }
}

function toServerDatetime(localValue) {
  // datetime-local gives "YYYY-MM-DDTHH:mm", we need "YYYY-MM-DD HH:mm:ss"
  if (!localValue) return ''
  return localValue.replace('T', ' ') + ':00'
}

async function addComment() {
  if (!newContent.value.trim() || sending.value) return

  // validate reminder ONLY if enabled
  if (addReminder.value) {
    if (!reminderDatetime.value) {
      reminderError.value = __('Reminder time is required')
      return
    }

    const when = new Date(reminderDatetime.value)
    if (!when || isNaN(when.getTime()) || when.getTime() <= Date.now()) {
      reminderError.value = __('Reminder must be in the future')
      return
    }
  }
  reminderError.value = ''

  sending.value = true
  error.value = ''
  try {
    // 1) أنشئ الكومنت using frappe.client.insert
    const ins = await call('frappe.client.insert', {
      doc: {
        doctype: 'Comment',
        reference_doctype: props.doctype,
        reference_name: props.name,
        // Format: Type:::Title
        subject: `${newType.value || 'Feedback'}:::${newTitle.value.trim()}`,
        content: newContent.value,
        comment_type: 'Comment',
      },
    })
    const commentName = ins?.name || ins?.message?.name || null

    // 2) ربط الريمايندر (اختياري)
    if (addReminder.value && reminderDatetime.value) {
      const desc = stripHtml(newContent.value)
      await call('crm.api.reminders.add_reminder', {
        doctype: props.doctype,
        name: props.name,
        remind_at: toServerDatetime(reminderDatetime.value),
        description: `Follow-up: "${desc.slice(0, 140)}${desc.length > 140 ? '…' : ''}"`,
        comment: commentName,
      })
      // 3) تنظيف delayed flags على كومنتاتي لنفس المستند
      try {
        await call('crm.api.reminders.clear_delayed_flags', {
          doctype: props.doctype,
          name: props.name,
        })
      } catch (_) {}
    }

    newContent.value = ''
    newTitle.value = ''
    newType.value = ''
    addReminder.value = false
    reminderDatetime.value = ''

    await resetAndLoad()
    toast.success(__('FeedBack added'))
    emit('update:show', false)
  } catch (e) {
    error.value = e?.messages?.[0] || e?.message || 'Failed to add FeedBack'
  } finally {
    sending.value = false
  }
}

function startEdit(c) {
  editing.value = { name: c.name, content: stripHtml(c.content), subject: c.subject || '' }
}

async function saveEdit() {
  if (!editing.value?.name || !editing.value.content?.trim()) return
  savingEdit.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'Comment',
      name: editing.value.name,
      fieldname: { subject: editing.value.subject || '', content: editing.value.content },
      value: '',
    })
    editing.value = null
    await resetAndLoad()
    toast.success(__('FeedBack updated'))
  } catch (e) {
    error.value = e?.message || 'Failed to update FeedBack'
  } finally {
    savingEdit.value = false
  }
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center p-4" role="dialog">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('update:show', false)"></div>

      <!-- Modal Content -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-visible flex flex-col max-h-[90vh]">
        
        <!-- Close Button -->
        <button 
          @click="emit('update:show', false)"
          class="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center shadow-md hover:bg-blue-600 transition-colors z-[110]"
        >
          <span class="text-xl font-bold">×</span>
        </button>

        <div class="p-6 overflow-y-auto">
          <div class="mb-6">
            <h2 class="text-2xl font-semibold text-gray-800">{{ __('Add Activity') }}</h2>
            <div class="mt-1 w-full border-b border-dashed border-gray-300"></div>
          </div>

          <div class="space-y-4">
            <!-- Activity Type -->
            <div class="relative">
              <select
                v-model="newType"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm appearance-none outline-none focus:border-blue-500 text-gray-700"
              >
                <option disabled value="">{{ __('Activity Type') }}</option>
                <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <!-- Title (Subject) -->
            <div>
              <input
                v-model="newTitle"
                type="text"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500 text-gray-700"
                :placeholder="__('Activity Title (optional)')"
              />
            </div>

            <!-- Reminder Section -->
            <div>
              <label class="inline-flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer select-none">
                <input type="checkbox" v-model="addReminder" class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <span>{{ __('Add a Reminder') }}</span>
              </label>

              <div v-if="addReminder" class="mt-3 relative">
                 <div class="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                  </div>
                  <input
                    type="datetime-local"
                    v-model="reminderDatetime"
                    class="w-full bg-white border border-gray-200 rounded-lg pl-11 pr-4 py-3 text-sm outline-none focus:border-blue-500 text-gray-700 cursor-pointer"
                  />
              </div>
            </div>

            <!-- Description Section -->
            <div>
              <label class="block text-sm font-medium text-gray-500 mb-2">{{ __('Description:') }}</label>
              <textarea
                v-model="newContent"
                rows="5"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500 text-gray-700 resize-none whitespace-pre-wrap"
                placeholder="Enter activity description..."
              ></textarea>
            </div>

            <!-- Error Message -->
            <div v-if="reminderError || error" class="text-xs text-red-600 px-1">
              {{ reminderError || error }}
            </div>

            <!-- Submit Button -->
            <div class="pt-2">
              <button
                @click="addComment"
                :disabled="sending"
                class="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white font-semibold py-4 rounded-xl transition-colors shadow-sm text-lg"
              >
                <span v-if="sending" class="flex items-center justify-center gap-2">
                  <Spinner class="h-5 w-5" />
                  {{ __('Saving...') }}
                </span>
                <span v-else>{{ __('Save Activity') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.prose :deep(p){ margin:0; }
</style>
