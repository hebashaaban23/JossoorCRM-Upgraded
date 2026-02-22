<template>
  <div class="relative w-full" @click.stop @mousedown.stop @dblclick.stop>
    <!-- العرض المختصر -->
    <div v-if="!open" class="flex items-center justify-between gap-2 overflow-hidden w-full h-8">
      <div class="truncate whitespace-nowrap text-ink-gray-9 flex-1 min-w-0 pr-2">
        {{ lastCommentText || __('No FeedBacks yet') }}
      </div>
      <button
        type="button"
        class="shrink-0 px-2 py-1 text-ink-blue-7 underline hover:no-underline text-sm"
        @click.stop="toggle(true)"
      >
        {{ __('Add') }}
      </button>
    </div>

    <!-- المودال -->
    <div v-else class="fixed inset-0 z-[100] flex items-start justify-center p-4 bg-black/40" @click="onBackdropClick">
      <div 
        class="relative mt-24 bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-visible"
        @click.stop
      >
        <!-- Close Button -->
        <button 
          @click.stop="toggle(false)"
          class="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center shadow-md hover:bg-blue-600 transition-colors z-[110]"
        >
          <span class="text-xl font-bold">×</span>
        </button>

        <div class="p-6">
          <div class="mb-6">
            <h2 class="text-2xl font-semibold text-gray-800">{{ __('Add Activity') }}</h2>
            <div class="mt-1 w-full border-b border-dashed border-gray-300"></div>
          </div>

          <form @submit.prevent="addComment" class="space-y-4">
            <!-- Activity Type -->
            <div class="relative">
              <select
                v-model="commentType"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm appearance-none outline-none focus:border-blue-500 text-gray-700"
                required
              >
                <option value="" disabled selected>{{ __('Activity Type') }}</option>
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

            <!-- Title -->
            <div>
              <input
                v-model="commentTitle"
                type="text"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500 text-gray-700"
                :placeholder="__('Activity Title (optional)')"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-500 mb-2">{{ __('Description:') }}</label>
              <textarea
                v-model="newComment"
                rows="5"
                class="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500 text-gray-700 resize-none whitespace-pre-wrap"
                placeholder="Enter activity description..."
                required
              ></textarea>
            </div>

            <!-- Error -->
            <div v-if="reminderError" class="text-xs text-red-600 px-1">
              {{ reminderError }}
            </div>

            <!-- Submit -->
            <div class="pt-2">
              <button
                type="submit"
                :disabled="saving || !canSubmit"
                class="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white font-semibold py-4 rounded-xl transition-colors shadow-sm text-lg"
              >
                <span v-if="saving">{{ __('Saving...') }}</span>
                <span v-else>{{ __('Save Activity') }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Button, call, toast } from 'frappe-ui'
import { formatDate } from '@/utils'
import { FEEDBACK_TYPES } from '@/constants/feedbackTypes'
const typeOptions = FEEDBACK_TYPES

const props = defineProps({
  leadName: { type: String, required: true },
  commentText: { type: String, default: '' },
})

const open = ref(false)
const loading = ref(false)
const saving  = ref(false)
const comments = ref([])
const newComment = ref('')
const commentTitle = ref('') // Title for the feedback
const commentType = ref('') // Default to empty for placeholder
const reminderDatetime = ref('')
const reminderError = ref('')
const addReminder = ref(false)

/** آخر Reminder على الليد (للعرض أو المنطق لاحقًا) */
const latestReminder = ref(null)

const lastCommentText = computed(() => {
  if (comments.value.length) {
    return stripHtml(comments.value[0].content || '')
  }
  return stripHtml(props.commentText || '')
})

const canSubmit = computed(() => {
  // comment required
  if (!newComment.value.trim()) return false
  // type required
  if (!commentType.value) return false

  // validate reminder ONLY if enabled
  if (addReminder.value) {
    if (!reminderDatetime.value) return false
    const dt = new Date(reminderDatetime.value)
    return dt && !isNaN(dt.getTime()) && dt.getTime() > Date.now()
  }
  return true
})

function parseSubject(subject='') {
  const [type, title] = subject.split(':::')
  return { type, title }
}

function stripHtml(html) {
  try {
    const div = document.createElement('div')
    div.innerHTML = html || ''
    return (div.textContent || div.innerText || '').trim()
  } catch {
    return html || ''
  }
}

function toDate(d, t) {
  try {
    if (!d || !t) return null
    const [date, time] = [d, t]
    const [y, mo, day] = date.split('-').map(x => parseInt(x, 10))
    const [hh, mm] = time.split(':').map(x => parseInt(x, 10))
    return new Date(y, (mo || 1)-1, day, hh || 0, mm || 0, 0, 0)
  } catch {
    return null
  }
}

function toServerDatetime(localValue) {
  if (!localValue) return ''
  return localValue.replace('T', ' ') + ':00'
}

function isDelayedFlag(comment) {
  const flag = comment?.delayed
  return flag === 1 || flag === true || flag === '1' || flag === 'Yes'
}

async function loadReminders() {
  latestReminder.value = null

  try {
    const res = await call('crm.api.comment.list_for_doc', {
      doctype: 'CRM Lead',
      name: props.leadName,
    })

    const list = Array.isArray(res?.message) ? res.message : res

    if (Array.isArray(list) && list.length) {
      const sorted = [...list].sort((a, b) =>
        a.remind_at > b.remind_at ? 1 : -1
      )
      latestReminder.value = sorted.at(-1)
    }

  } catch (e) {
    console.error("Failed to load reminders:", e)
  }
}

/* ===== Comments ===== */
async function refreshDelayedState() {
  try {
    await call('crm.api.reminders.recalc_delayed_for_doc', {
      doctype: 'CRM Lead',
      name: props.leadName,
    })
  } catch (e) {
    // احتمالات: غياب الحقل أو عدم توافر الصلاحيات
    console.debug('recalc_delayed_for_doc failed', e)
  }
}

async function loadComments() {
  loading.value = true
  try {
    const res = await call('crm.api.comment.list_for_doc', {
      doctype: 'CRM Lead',
      name: props.leadName,
    })

    comments.value = Array.isArray(res?.message)
      ? res.message
      : (Array.isArray(res) ? res : [])

  } finally {
    loading.value = false
  }
}


function onBackdropClick(e) { if (e.target === e.currentTarget) toggle(false) }
async function toggle(v) {
  open.value = v
  if (v) {
    reminderError.value = ''
    reminderDatetime.value = ''
    commentType.value = ''
    addReminder.value = false
    await refreshDelayedState()
    await Promise.all([loadComments(), loadReminders()])
  }
}

/* ===== Submit ===== */
async function addComment() {

  if (saving.value) return
  const content = newComment.value.trim()
  if (!content) return

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

  saving.value = true
  reminderError.value = ''

  try {

    // ✅ SAME METHOD USED INTERNALLY BY FRAPPE
    const res = await call('frappe.client.insert', {
      doc: {
        doctype: 'Comment',
        comment_type: 'Comment',

        reference_doctype: 'CRM Lead',
        reference_name: props.leadName,
        content: content,
        // Format: Type:::Title:::EventTime
        subject: `${commentType.value}:::${commentTitle.value || ''}`,
      }
    })

    const commentName = res?.message?.name || res?.name

    // ✅ reminder (UNCHANGED)
    if (addReminder.value && reminderDatetime.value) {
      await call('crm.api.reminders.add_reminder', {
        doctype: 'CRM Lead',
        name: props.leadName,
        remind_at: toServerDatetime(reminderDatetime.value),
        description: content.slice(0,140),
        comment: commentName,
      })
    }

    toast.success(__('FeedBack added'))
    toggle(false)

    newComment.value = ''
    commentTitle.value = ''
    reminderDatetime.value = ''
    addReminder.value = false
    commentType.value = ''


    await Promise.all([
      loadComments(),
      loadReminders()
    ])

  } catch (e) {

    toast.error(
      e?.messages?.[0] ||
      e?.message ||
      __('Failed to add feedback')
    )

  } finally {
    saving.value = false
  }
}

// Data is fetched via toggle() when user clicks "Add"
</script>
