<template>
  <div v-if="leadData" class="flex flex-col gap-6 p-6">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-7xl mx-auto w-full">
      <!-- Card 1: Location & Type -->
      <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-6 flex flex-col h-full">
        <h3 class="text-lg font-bold text-gray-800 mb-6">{{ __('Location & Type') }}</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div v-for="fieldName in card1FieldNames" :key="fieldName">
            <Field v-if="getField(fieldName)" :field="getField(fieldName)" />
          </div>
        </div>
      </div>

      <!-- Card 2: Property Details -->
      <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-6 flex flex-col h-full">
        <h3 class="text-lg font-bold text-gray-800 mb-6">{{ __('Property Details') }}</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div v-for="fieldName in card2FieldNames" :key="fieldName">
            <Field v-if="getField(fieldName)" :field="getField(fieldName)" />
          </div>
        </div>
      </div>

      <!-- Card 3: Features & Financial -->
      <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-6 flex flex-col h-full">
        <h3 class="text-lg font-bold text-gray-800 mb-6">{{ __('Features & Financial') }}</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div v-for="fieldName in card3FieldNames" :key="fieldName">
            <Field v-if="getField(fieldName)" :field="getField(fieldName)" />
          </div>
        </div>
      </div>

      <!-- Card 4: Slideable Notes -->
      <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-6 flex flex-col h-full overflow-hidden">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-gray-800">{{ __('Notes') }}</h3>
            <span v-if="notes.length > 1" class="text-xs text-gray-400 font-medium">({{ currentNoteIndex + 1 }} / {{ notes.length }})</span>
          </div>
          <div class="flex items-center gap-2">
            <template v-if="notes.length > 1">
               <Button variant="ghost" @click="prevNote" :disabled="currentNoteIndex === 0">
                 <template #icon><FeatherIcon name="chevron-left" class="h-5 w-5" /></template>
               </Button>
               <Button variant="ghost" @click="nextNote" :disabled="currentNoteIndex === notes.length - 1">
                 <template #icon><FeatherIcon name="chevron-right" class="h-5 w-5" /></template>
               </Button>
            </template>
            <Button variant="ghost" class="hover:bg-gray-50" @click="showCreateNoteModal = true">
              <template #icon><FeatherIcon name="plus" class="h-6 w-6 text-blue-500" /></template>
            </Button>
          </div>
        </div>
        
        <div v-if="currentNote" class="bg-gray-50 rounded-xl p-5 flex-1 flex flex-col transition-all duration-300">
          <div class="text-[15px] text-gray-700 leading-relaxed overflow-y-auto flex-1 mb-4 scrollbar-hide">
            <div class="font-bold text-sm text-gray-800 mb-2" v-if="currentNote.title">{{ currentNote.title }}</div>
            <div v-html="currentNote.content" class="prose prose-sm max-w-none"></div>
          </div>
          <div class="flex items-center justify-between text-[11px] text-gray-400 border-t border-gray-200/60 pt-3 mt-auto shrink-0 font-medium">
            <div class="flex items-center gap-1.5">
              <span class="opacity-70">{{ __('Date:') }}</span>
              <span class="text-gray-500">{{ formatDate(currentNote.creation) }}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="opacity-70">{{ __('Agent:') }}</span>
              <span class="text-gray-500">{{ currentNote.owner_name }}</span>
            </div>
          </div>
        </div>
        <div v-else class="flex flex-col items-center justify-center flex-1 text-gray-400 py-10">
          <NoteIcon class="h-10 w-10 opacity-10 mb-2" />
          <span class="text-sm italic opacity-60">{{ __('No notes added yet') }}</span>
        </div>
      </div>
    </div>

    <!-- Simple Note Creation Modal -->
    <Dialog v-model="showCreateNoteModal" :options="{ title: __('Add Note'), size: 'sm' }">
        <template #body-content>
            <div class="p-4 space-y-4">
                <FormControl type="text" :placeholder="__('Title')" v-model="newNote.title" />
                <FormControl type="textarea" :placeholder="__('Note content...')" v-model="newNote.content" rows="6" />
            </div>
        </template>
        <template #actions>
            <Button variant="solid" :label="__('Add Note')" :loading="savingNote" @click="addNote" />
            <Button variant="ghost" :label="__('Cancel')" @click="showCreateNoteModal = false" />
        </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, provide, toRef, watch } from 'vue'
import { call, Button, Dialog, FormControl, toast, FeatherIcon } from 'frappe-ui'
import { formatDate } from '@/utils'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import Field from '@/components/FieldLayout/Field.vue'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'

const props = defineProps({
  leadData: Object,
  docname: String,
})

const { getUser } = usersStore()
const { doctypeMeta } = getMeta('CRM Lead')

const fieldsArr = computed(() => doctypeMeta['CRM Lead']?.fields || [])

function getField(fieldname) {
    return fieldsArr.value.find(f => f.fieldname === fieldname)
}

// Provide context for Field.vue
provide('data', toRef(props, 'leadData'))
provide('doctype', 'CRM Lead')
provide('preview', ref(false))
provide('isGridRow', ref(false))

const showCreateNoteModal = ref(false)
const savingNote = ref(false)
const notes = ref([])
const currentNoteIndex = ref(0)
const currentNote = computed(() => notes.value[currentNoteIndex.value] || null)

const newNote = reactive({
    title: '',
    content: ''
})

const card1FieldNames = [
  'property_city',
  'property_region',
  'property_type',
  'property_subtype',
  'property_relation',
  'property_project',
]

const card2FieldNames = [
  'property_space',
  'property_floor',
  'property_bedrooms',
  'property_bathrooms',
  'property_condition',
  'property_decoration',
  'property_year_built',
  'property_delivery_date',
]

const card3FieldNames = [
  'property_view',
  'property_finishing',
  'property_features',
  'property_min_price',
  'property_max_price',
  'property_payment',
  'property_down_payment',
  'property_ownership',
]

async function fetchNotes() {
  try {
    const res = await call('crm.api.activities.get_activities', { name: props.docname })
    // The API returns [activities, calls, notes, tasks, attachments]
    const notesData = res[2] || []
    // Descending order sort (latest first)
    notes.value = notesData.sort((a, b) => new Date(b.creation) - new Date(a.creation)).map(n => ({
      ...n,
      owner_name: getUser(n.owner).full_name || n.owner
    }))
    currentNoteIndex.value = 0
  } catch (e) {
    console.error('Failed to fetch notes', e)
  }
}

function nextNote() {
  if (currentNoteIndex.value < notes.value.length - 1) {
    currentNoteIndex.value++
  }
}

function prevNote() {
  if (currentNoteIndex.value > 0) {
    currentNoteIndex.value--
  }
}

async function addNote() {
    if (!newNote.content.trim()) return
    savingNote.value = true
    try {
        await call('frappe.client.insert', {
            doc: {
                doctype: 'FCRM Note',
                title: newNote.title || 'Note',
                content: newNote.content,
                reference_docname: props.docname
            }
        })
        newNote.title = ''
        newNote.content = ''
        showCreateNoteModal.value = false
        toast.success(__('Note added'))
        await fetchNotes()
    } catch (e) {
        toast.error(__('Failed to add note'))
    } finally {
        savingNote.value = false
    }
}

onMounted(() => {
  fetchNotes()
})

// Refresh notes when docname changes
watch(() => props.docname, () => {
  fetchNotes()
})
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>
