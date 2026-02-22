<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <div class="flex flex-col p-6 gap-8 bg-white rounded-xl max-h-[90vh] overflow-y-auto">

        <!-- ── Header ── -->
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-800">{{ __('Add New Lead') }}</h2>
            <p class="text-sm text-gray-400 mt-0.5">{{ __('Fill in the details below to create a new lead') }}</p>
          </div>
          <button @click="show = false"
            class="w-9 h-9 flex items-center justify-center rounded-full bg-[#4A90E2] hover:bg-[#3B7DCC] transition-colors text-white text-lg font-bold shadow">
            ×
          </button>
        </div>

        <!-- ══════════════════════════════════════════════
             SECTION 1 — Lead Information
        ══════════════════════════════════════════════ -->
        <section>
          <SectionHeader :title="__('Lead Information')" />

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4 mt-6">

            <!-- salutation → Link: Salutation (backend) -->
            <FieldWrap :label="__('Title')">
              <SelectField v-model="lead.doc.salutation"
                :options="salutations.data?.map(s => s.name) ?? []"
                :placeholder="__('Select...')" />
            </FieldWrap>

            <!-- first_name → Data, reqd -->
            <FieldWrap :label="__('First Name')" required>
              <input v-model="lead.doc.first_name" type="text" class="fi"
                :class="{ 'border-red-400 bg-red-50': fieldError === 'first_name' }" />
            </FieldWrap>

            <!-- last_name → Data -->
            <FieldWrap :label="__('Last Name')">
              <input v-model="lead.doc.last_name" type="text" class="fi" />
            </FieldWrap>

            <!-- gender → Link: Gender — rendered as radios -->
            <FieldWrap :label="__('Gender')">
              <div class="flex gap-4 h-10 items-center">
                <RadioBtn v-model="lead.doc.gender" value="Male"   :label="__('Male')"   name="gender" />
                <RadioBtn v-model="lead.doc.gender" value="Female" :label="__('Female')" name="gender" />
              </div>
            </FieldWrap>

            <!-- email → Data/Email -->
            <FieldWrap :label="__('Email')">
              <input v-model="lead.doc.email" type="email" class="fi"
                :class="{ 'border-red-400 bg-red-50': fieldError === 'email' }" />
            </FieldWrap>

            <!-- mobile_no → Data/Phone, reqd -->
            <FieldWrap :label="__('Mobile No')" required>
              <input v-model="lead.doc.mobile_no" type="tel" class="fi"
                :class="{ 'border-red-400 bg-red-50': fieldError === 'mobile_no' }" />
            </FieldWrap>

            <!-- phone → Data/Phone -->
            <FieldWrap :label="__('Other Phone')">
              <input v-model="lead.doc.phone" type="tel" class="fi" />
            </FieldWrap>

            <!-- source → Link: CRM Lead Source (backend) -->
            <FieldWrap :label="__('Source')">
              <SelectField v-model="lead.doc.source"
                :options="leadSources.data?.map(s => s.name) ?? []"
                :placeholder="__('Select...')" />
            </FieldWrap>

            <!-- territory → Link: CRM Territory (backend) -->
            <FieldWrap :label="__('Territory')">
              <SelectField v-model="lead.doc.territory"
                :options="territories.data?.map(t => t.name) ?? []"
                :placeholder="__('Select...')" />
            </FieldWrap>

            <!-- industry → Link: CRM Industry (backend) -->
            <FieldWrap :label="__('Industry')">
              <SelectField v-model="lead.doc.industry"
                :options="industries.data?.map(i => i.name) ?? []"
                :placeholder="__('Select...')" />
            </FieldWrap>

            <!-- lead_type → Select (OPT.lead_type from embedded JSON) -->
            <FieldWrap :label="__('Lead Type')">
              <div class="flex gap-4 h-10 items-center">
                <RadioBtn v-for="opt in OPT.lead_type" :key="opt"
                  v-model="lead.doc.lead_type" :value="opt" :label="__(opt)" name="lead_type" />
              </div>
            </FieldWrap>

            <!-- lead_owner → Link: User (auto-set, read-only) -->
            <FieldWrap :label="__('Lead Owner')">
              <input v-model="lead.doc.lead_owner" type="text"
                class="fi bg-gray-50 text-gray-400 cursor-not-allowed" disabled />
            </FieldWrap>

          </div>

          <!-- Unit Assignment sub-row -->
          <div class="mt-4 pt-4 border-t border-gray-100">
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
              {{ __('Unit Assignment') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4">

              <!-- project → Link: Real Estate Project (backend) -->
              <FieldWrap :label="__('Project')">
                <SelectField
                  v-model="lead.doc.project"
                  :options="projects.data?.map(p => ({ value: p.name, label: p.project_name || p.name })) ?? []"
                  :placeholder="__('Select...')"
                  @update:modelValue="onLeadProjectChange"
                />
              </FieldWrap>

              <!-- project_unit → Link: Project Unit — filtered by project (backend) -->
              <FieldWrap :label="__('Project Unit')">
                <SelectField
                  v-model="lead.doc.project_unit"
                  :options="filteredProjectUnits.map(u => ({ value: u.name, label: u.unit_name || u.name }))"
                  :placeholder="__('Select...')"
                  :disabled="!lead.doc.project"
                />
              </FieldWrap>

              <!-- single_unit → Link: Unit (backend) -->
              <FieldWrap :label="__('Single Unit')">
                <SelectField
                  v-model="lead.doc.single_unit"
                  :options="units.data?.map(u => ({ value: u.name, label: u.unit_name || u.name })) ?? []"
                  :placeholder="__('Select...')"
                />
              </FieldWrap>

            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════════
             SECTION 2 — Property Preference
        ══════════════════════════════════════════════ -->
        <section>
          <SectionHeader :title="__('Property Preference')" />

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

            <!-- ── Card: Core Preference ── -->
            <PropCard :title="__('Core Preference')">

              <!-- property_city → Select — OPT.property_city -->
              <FieldWrap :label="__('City')">
                <SelectField v-model="lead.doc.property_city"
                  :options="OPT.property_city" :placeholder="__('Select...')" />
              </FieldWrap>

              <!-- property_region → Select — OPT.property_region -->
              <FieldWrap :label="__('Region / District')">
                <SelectField v-model="lead.doc.property_region"
                  :options="OPT.property_region" :placeholder="__('Select...')" />
              </FieldWrap>

              <!-- property_type → Select — OPT.property_type, rendered as chips -->
              <FieldWrap :label="__('Property Type')">
                <div class="flex gap-2 flex-wrap">
                  <TypeChip v-for="t in OPT.property_type" :key="t"
                    v-model="lead.doc.property_type" :value="t" :label="__(t)"
                    @update:modelValue="lead.doc.property_subtype = ''" />
                </div>
              </FieldWrap>

              <!-- property_subtype → Select — SUBTYPES_BY_TYPE[type] subset -->
              <FieldWrap :label="__('Property Subtype')">
                <SelectField
                  v-model="lead.doc.property_subtype"
                  :options="currentSubtypes"
                  :placeholder="lead.doc.property_type ? __('Select...') : __('Select a type first')"
                  :disabled="!lead.doc.property_type"
                />
              </FieldWrap>

              <!-- property_space → Int — slider, writes raw sqm value -->
              <FieldWrap :label="__('Space (sqm)')">
                <Slider v-model="lead.doc.property_space"
                  :max="SPACE_MAX" :format="v => v + ' m²'" />
              </FieldWrap>

              <!-- property_floor → Select — OPT.property_floor -->
              <FieldWrap :label="__('Floor Preference')">
                <SelectField v-model="lead.doc.property_floor"
                  :options="OPT.property_floor" :placeholder="__('Select...')" />
              </FieldWrap>

            </PropCard>

            <!-- ── Card: Property Details ── -->
            <PropCard :title="__('Property Details')">

              <!-- property_condition → Select — OPT.property_condition, rendered as radios -->
              <FieldWrap :label="__('Condition')">
                <div class="flex flex-col gap-1.5">
                  <RadioBtn v-for="c in OPT.property_condition" :key="c"
                    v-model="lead.doc.property_condition" :value="c" :label="__(c)" name="condition" />
                </div>
              </FieldWrap>

              <!-- property_decoration → Select — OPT.property_decoration -->
              <FieldWrap :label="__('Decoration Status')">
                <SelectField v-model="lead.doc.property_decoration"
                  :options="OPT.property_decoration" :placeholder="__('Select...')" />
              </FieldWrap>

              <!-- property_finishing → Select — OPT.property_finishing -->
              <FieldWrap :label="__('Finishing Level')">
                <SelectField v-model="lead.doc.property_finishing"
                  :options="OPT.property_finishing" :placeholder="__('Select...')" />
              </FieldWrap>

              <!-- property_relation → Select — OPT.property_relation, chips -->
              <FieldWrap :label="__('Property Relation')">
                <div class="flex gap-2 flex-wrap mb-2">
                  <TypeChip v-for="r in OPT.property_relation" :key="r"
                    v-model="lead.doc.property_relation" :value="r" :label="__(r)"
                    @update:modelValue="v => { if (v !== 'Project') lead.doc.property_project = '' }" />
                </div>
                <input v-if="lead.doc.property_relation === 'Project'"
                  v-model="lead.doc.property_project"
                  type="text" class="fi" :placeholder="__('Enter project name...')" />
              </FieldWrap>

              <!-- property_year_built → Int -->
              <FieldWrap :label="__('Year Built')">
                <input v-model.number="lead.doc.property_year_built" type="number"
                  min="1900" :max="currentYear" class="fi" placeholder="e.g. 2022" />
              </FieldWrap>

              <!-- property_delivery_date → Date -->
              <FieldWrap :label="__('Expected Delivery Date')">
                <input v-model="lead.doc.property_delivery_date" type="date" class="fi" />
              </FieldWrap>

              <!-- property_view → Select — OPT.property_view -->
              <FieldWrap :label="__('View Preference')">
                <SelectField v-model="lead.doc.property_view"
                  :options="OPT.property_view" :placeholder="__('Select...')" />
              </FieldWrap>

              <!-- property_features → Select — OPT.property_features -->
              <FieldWrap :label="__('Key Feature')">
                <SelectField v-model="lead.doc.property_features"
                  :options="OPT.property_features" :placeholder="__('Select...')" />
              </FieldWrap>

            </PropCard>

            <!-- ── Column 3: Rooms + Financial + Notes ── -->
            <div class="flex flex-col gap-5">

              <!-- Room Details card -->
              <PropCard :title="__('Room Details')">
                <div class="grid grid-cols-2 gap-4">
                  <!-- property_bedrooms → Select — OPT.property_bedrooms -->
                  <FieldWrap :label="__('Bedrooms')">
                    <SelectField v-model="lead.doc.property_bedrooms"
                      :options="OPT.property_bedrooms" :placeholder="__('Any')" />
                  </FieldWrap>
                  <!-- property_bathrooms → Select — OPT.property_bathrooms -->
                  <FieldWrap :label="__('Bathrooms')">
                    <SelectField v-model="lead.doc.property_bathrooms"
                      :options="OPT.property_bathrooms" :placeholder="__('Any')" />
                  </FieldWrap>
                </div>
              </PropCard>

              <!-- Financial Preference card -->
              <PropCard :title="__('Financial Preference')">

                <!-- property_min_price → Currency — slider -->
                <FieldWrap :label="__('Min Budget')">
                  <Slider v-model="lead.doc.property_min_price"
                    :max="PRICE_MAX" :format="formatPrice" />
                </FieldWrap>

                <!-- property_max_price → Currency — slider -->
                <FieldWrap :label="__('Max Budget')">
                  <Slider v-model="lead.doc.property_max_price"
                    :max="PRICE_MAX" :format="formatPrice" />
                </FieldWrap>

                <!-- property_payment → Select — OPT.property_payment, chips -->
                <FieldWrap :label="__('Payment Method')">
                  <div class="flex flex-wrap gap-2">
                    <TypeChip v-for="p in OPT.property_payment" :key="p"
                      v-model="lead.doc.property_payment" :value="p" :label="__(p)" />
                  </div>
                </FieldWrap>

                <!-- property_down_payment → Percent — shown only when payment is not first option -->
                <FieldWrap
                  v-if="lead.doc.property_payment && lead.doc.property_payment !== OPT.property_payment[0]"
                  :label="__('Down Payment (%)')">
                  <input v-model.number="lead.doc.property_down_payment"
                    type="number" min="0" max="100" step="5" class="fi" placeholder="e.g. 20" />
                </FieldWrap>

                <!-- property_ownership → Select — OPT.property_ownership, chips -->
                <FieldWrap :label="__('Ownership Type')">
                  <div class="flex flex-wrap gap-2">
                    <TypeChip v-for="o in OPT.property_ownership" :key="o"
                      v-model="lead.doc.property_ownership" :value="o" :label="__(o)" />
                  </div>
                </FieldWrap>

              </PropCard>

              <!-- Notes → Text Editor -->
              <PropCard :title="__('Notes')">
                <textarea v-model="lead.doc.notes"
                  class="w-full border border-gray-200 rounded-lg p-3 text-sm text-gray-700
                         resize-none focus:outline-none focus:border-[#4A90E2] transition-colors"
                  rows="4" :placeholder="__('Add any additional notes...')" />
              </PropCard>

            </div>
          </div>
        </section>

        <!-- ── Footer ── -->
        <div class="flex items-center justify-between pt-4 border-t border-gray-100">
          <p v-if="error" class="text-sm text-red-500 flex items-center gap-1.5">
            <span>⚠</span> {{ __(error) }}
          </p>
          <div v-else />
          <div class="flex gap-3">
            <button @click="show = false"
              class="px-6 py-2 rounded-lg border border-[#4A90E2] text-[#4A90E2] font-semibold
                     text-sm hover:bg-blue-50 transition-colors">
              {{ __('Cancel') }}
            </button>
            <button @click="createNewLead" :disabled="isLeadCreating"
              class="px-6 py-2 rounded-lg bg-[#4A90E2] text-white font-semibold text-sm
                     hover:bg-[#3B7DCC] transition-colors disabled:opacity-50
                     disabled:cursor-not-allowed flex items-center gap-2">
              <span v-if="isLeadCreating"
                class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              {{ isLeadCreating ? __('Saving...') : __('Add Lead') }}
            </button>
          </div>
        </div>

      </div>
    </template>
  </Dialog>
</template>

<script setup>
// ─── Framework & app imports ─────────────────────────────────────────────────
import { usersStore }    from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { sessionStore }  from '@/stores/session'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture }       from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument }   from '@/data/document'
import {
  computed, defineComponent, h,
  onMounted, ref, nextTick,
} from 'vue'
import { useRouter } from 'vue-router'

// ─── Props / stores ──────────────────────────────────────────────────────────
const props = defineProps({ defaults: Object })

const { user }    = sessionStore()
const { getUser } = usersStore()
const { statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show           = defineModel()
const router         = useRouter()
const error          = ref(null)
const fieldError     = ref(null)
const isLeadCreating = ref(false)
const currentYear    = new Date().getFullYear()

const SPACE_MAX = 500        // property_space Int max (sqm)
const PRICE_MAX = 5_000_000  // property_min/max_price max (EGP)

function formatPrice(val) {
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M EGP'
  if (val >= 1_000)     return (val / 1_000).toFixed(0) + 'K EGP'
  return val + ' EGP'
}

// ═══════════════════════════════════════════════════════════════════════════════
// Parse CRM Lead doctype JSON to extract ALL Select field options
// This runs once at module load — zero hard-coding, zero external file needed.
// ═══════════════════════════════════════════════════════════════════════════════

const DOCTYPE_JSON = {
  "fields": [
    {"fieldname": "naming_series", "fieldtype": "Select", "options": "CRM-LEAD-.YYYY.-"},
    {"fieldname": "no_of_employees", "fieldtype": "Select", "options": "1-10\n11-50\n51-200\n201-500\n501-1000\n1000+"},
    {"fieldname": "lead_type", "fieldtype": "Select", "options": "\nOut Source\nCompany"},
    {"fieldname": "property_city", "fieldtype": "Select", "options": "\nCairo\nNew Cairo\nNasr City\nHeliopolis\nMaadi\n6th of October\nSheikh Zayed\nZamalek\nNew Administrative Capital\nAlexandria\nGiza"},
    {"fieldname": "property_region", "fieldtype": "Select", "options": "\nMaadi\nDegla\nSarayat\nZohour\nNew Maadi\nHeliopolis\nNasr City\nMadinet Nasr\nZamalek\nGarden City\nDowntown Cairo\nMohandessin\nAgouza\nDokki\nShoubra\nShubra El Kheima\nNew Cairo - 1st Settlement\nNew Cairo - 5th Settlement\nNew Cairo - 3rd Settlement\nBeit El Watan\nAl Rehab City\nMadinaty\nMostakbal City\nAl Shorouk City\nAl Obour City\nNew Administrative Capital - R1\nNew Administrative Capital - R2\nNew Administrative Capital - R3\n6th of October - Hay 1\n6th of October - Hay 2\n6th of October - Hay 3\nSheikh Zayed - Hay 1\nSheikh Zayed - Hay 2\nNorth Coast\nAin Sokhna\nEl Gouna\nHurghada\nSharm El Sheikh"},
    {"fieldname": "property_type", "fieldtype": "Select", "options": "\nResidential\nCommercial\nAdministrative\nLand"},
    {"fieldname": "property_subtype", "fieldtype": "Select", "options": "\nApartment\nDuplex\nPenthouse\nStudio\nVilla\nTwin House\nTownhouse\nChalet\nCabin\nOffice\nShop\nClinic\nWarehouse\nShowroom\nAdministrative Office\nPlot - Residential\nPlot - Commercial\nPlot - Industrial"},
    {"fieldname": "property_floor", "fieldtype": "Select", "options": "\nGround Floor\n1st Floor\n2nd Floor\n3rd Floor\n4th Floor\n5th Floor\n6th Floor\n7th Floor\n8th Floor\n9th Floor\n10th Floor\nHigh Floor (10+)\nRooftop / Penthouse\nBasement\nNo Preference"},
    {"fieldname": "property_condition", "fieldtype": "Select", "options": "\nNew / Off-Plan\nUnder Construction\nReady to Move\nRenovated\nNeed Repair\nOld Building"},
    {"fieldname": "property_decoration", "fieldtype": "Select", "options": "\nFurnished\nSemi-Furnished\nUnfurnished\nCore & Shell\nSemi-Finished\nFully Finished\nSuper Lux\nUltra Lux"},
    {"fieldname": "property_relation", "fieldtype": "Select", "options": "\nStand Alone\nProject\nCompound"},
    {"fieldname": "property_bedrooms", "fieldtype": "Select", "options": "\nStudio\n1\n2\n3\n4\n5\n6+"},
    {"fieldname": "property_bathrooms", "fieldtype": "Select", "options": "\n1\n2\n3\n4\n5+"},
    {"fieldname": "property_view", "fieldtype": "Select", "options": "\nStreet View\nGarden View\nPool View\nLake View\nSea View\nCity View\nNo Preference"},
    {"fieldname": "property_finishing", "fieldtype": "Select", "options": "\nCore & Shell\nSemi-Finished\nFully Finished\nSuper Lux\nUltra Lux"},
    {"fieldname": "property_features", "fieldtype": "Select", "options": "\nPrivate Garden\nPrivate Pool\nShared Pool\nGym\nGarage\nElevator\nSecurity / Gated\nSmart Home\nSea Access\nLake / Lagoon\nGolf Course View\nPet Friendly\nStorage Room\nMaid Room\nDriver Room"},
    {"fieldname": "property_payment", "fieldtype": "Select", "options": "\nCash\nInstallment\nMortgage\nBank Loan"},
    {"fieldname": "property_ownership", "fieldtype": "Select", "options": "\nBuy\nRent\nRent-to-Own"},
    {"fieldname": "sla_status", "fieldtype": "Select", "options": "\nFirst Response Due\nRolling Response Due\nFailed\nFulfilled"}
  ]
}

// Parse options from the embedded JSON
function parseSelectOptions(doctypeJson) {
  const opts = {}
  for (const field of doctypeJson.fields) {
    if (field.fieldtype === 'Select' && field.options) {
      const lines = field.options.split('\n').filter(s => s.trim())
      opts[field.fieldname] = lines
    }
  }
  return opts
}

const OPT = parseSelectOptions(DOCTYPE_JSON)

// Build subtype groupings from the full list
const SUBTYPES_BY_TYPE = {
  Residential:    ['Apartment', 'Duplex', 'Penthouse', 'Studio', 'Villa', 'Twin House', 'Townhouse', 'Chalet', 'Cabin'],
  Commercial:     ['Shop', 'Showroom', 'Warehouse'],
  Administrative: ['Office', 'Administrative Office', 'Clinic'],
  Land:           ['Plot - Residential', 'Plot - Commercial', 'Plot - Industrial'],
}

// Filtered subtypes based on selected property_type
const currentSubtypes = computed(() =>
  lead.doc?.property_type ? (SUBTYPES_BY_TYPE[lead.doc.property_type] ?? []) : []
)

// ═══════════════════════════════════════════════════════════════════════════════
// Inline sub-components (self-contained, no extra files needed)
// ═══════════════════════════════════════════════════════════════════════════════

const SectionHeader = defineComponent({
  props: { title: String },
  setup(p) {
    return () => h('div', { class: 'flex items-center gap-3 mb-1' }, [
      h('span', { class: 'text-xs font-bold uppercase tracking-widest text-[#4A90E2]' }, p.title),
      h('div',  { class: 'flex-1 h-px bg-gradient-to-r from-[#4A90E2]/30 to-transparent' }),
    ])
  },
})

const PropCard = defineComponent({
  props: { title: String },
  setup(p, { slots }) {
    return () => h('div', {
      class: 'border border-gray-100 rounded-xl p-5 flex flex-col gap-4 bg-white shadow-sm',
    }, [
      h('div', { class: 'flex flex-col gap-1' }, [
        h('p',   { class: 'font-semibold text-sm text-gray-600' }, p.title),
        h('div', { class: 'w-12 h-0.5 bg-[#4A90E2]/40 rounded' }),
      ]),
      slots.default?.(),
    ])
  },
})

const FieldWrap = defineComponent({
  props: { label: String, required: Boolean },
  setup(p, { slots }) {
    return () => h('div', { class: 'flex flex-col gap-1' }, [
      h('label', { class: 'text-xs font-semibold text-gray-500 flex items-center gap-1' }, [
        p.label,
        p.required ? h('span', { class: 'text-red-400' }, '*') : null,
      ]),
      slots.default?.(),
    ])
  },
})

const RadioBtn = defineComponent({
  props: { modelValue: String, value: String, label: String, name: String },
  emits: ['update:modelValue'],
  setup(p, { emit }) {
    return () => h('label', { class: 'flex items-center gap-1.5 cursor-pointer group' }, [
      h('input', {
        type: 'radio', name: p.name, value: p.value,
        checked: p.modelValue === p.value,
        onChange: () => emit('update:modelValue', p.value),
        class: 'w-4 h-4 accent-[#4A90E2]',
      }),
      h('span', { class: 'text-sm text-gray-700 group-hover:text-[#4A90E2] transition-colors' }, p.label),
    ])
  },
})

const TypeChip = defineComponent({
  props: { modelValue: String, value: String, label: String },
  emits: ['update:modelValue'],
  setup(p, { emit }) {
    return () => h('button', {
      type: 'button',
      onClick: () => emit('update:modelValue', p.modelValue === p.value ? '' : p.value),
      class: [
        'px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-150',
        p.modelValue === p.value
          ? 'bg-[#4A90E2] text-white border-[#4A90E2] shadow-sm'
          : 'bg-white text-gray-500 border-gray-200 hover:border-[#4A90E2] hover:text-[#4A90E2]',
      ].join(' '),
    }, p.label)
  },
})

/**
 * SelectField — unified select for both:
 *   - string[] options  (Select fields from OPT)
 *   - { value, label }[] options  (Link fields from backend)
 */
const SelectField = defineComponent({
  props: {
    modelValue:  String,
    options:     { type: Array, default: () => [] },
    placeholder: { type: String, default: 'Select...' },
    disabled:    { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(p, { emit }) {
    return () => h('select', {
      value: p.modelValue ?? '',
      disabled: p.disabled,
      onChange: e => emit('update:modelValue', e.target.value),
      class: [
        'select-fi fi',
        p.disabled ? 'bg-gray-50 text-gray-300 cursor-not-allowed' : '',
      ].join(' '),
    }, [
      h('option', { value: '' }, p.placeholder),
      ...(p.options ?? []).map(o =>
        typeof o === 'string'
          ? h('option', { value: o }, o)
          : h('option', { value: o.value }, o.label)
      ),
    ])
  },
})

/** Slider — draggable, writes raw numeric value directly to the field */
const Slider = defineComponent({
  props: {
    modelValue: { type: Number, default: 0 },
    max:        { type: Number, default: 100 },
    format:     { type: Function, default: v => v },
  },
  emits: ['update:modelValue'],
  setup(p, { emit }) {
    const trackRef = ref(null)
    const dragging = ref(false)
    const pct = computed(() =>
      Math.min(100, Math.max(0, ((p.modelValue ?? 0) / p.max) * 100))
    )

    function applyPos(clientX) {
      const el = trackRef.value
      if (!el) return
      const rect = el.getBoundingClientRect()
      const pc = Math.min(100, Math.max(0, (clientX - rect.left) / rect.width * 100))
      emit('update:modelValue', Math.round((pc / 100) * p.max))
    }

    function startDrag(e) {
      e.preventDefault()
      dragging.value = true
      applyPos(e.clientX)
      const move = e => { if (dragging.value) applyPos(e.clientX) }
      const up   = () => {
        dragging.value = false
        document.removeEventListener('mousemove', move)
        document.removeEventListener('mouseup', up)
      }
      document.addEventListener('mousemove', move)
      document.addEventListener('mouseup', up)
    }

    return () => {
      const val = p.modelValue ?? 0
      const pc  = pct.value
      return h('div', { class: 'flex flex-col gap-2 pt-5' }, [
        h('div', { class: 'relative' }, [
          h('div', {
            ref: trackRef, onMousedown: startDrag,
            class: 'w-full h-2 bg-gray-200 rounded-full cursor-pointer select-none relative',
          }, [
            h('div', { class: 'absolute h-2 bg-[#4A90E2] rounded-full pointer-events-none', style: { width: pc + '%' } }),
            h('div', {
              class: 'absolute w-4 h-4 bg-white border-2 border-[#4A90E2] rounded-full shadow -translate-y-1 -translate-x-1/2 pointer-events-none',
              style: { left: pc + '%', top: '0' },
            }),
          ]),
          h('div', {
            class: 'absolute -top-6 -translate-x-1/2 bg-[#4A90E2] text-white text-[10px] rounded px-1.5 py-0.5 pointer-events-none whitespace-nowrap',
            style: { left: pc + '%' },
          }, p.format(val)),
        ]),
        h('div', { class: 'flex justify-between text-[10px] text-gray-400' }, [
          h('span', p.format(0)),
          h('span', p.format(p.max)),
        ]),
      ])
    }
  },
})

// ─── Project units filter ─────────────────────────────────────────────────────
function onLeadProjectChange() { lead.doc.project_unit = '' }

const filteredProjectUnits = computed(() => {
  if (!lead.doc?.project || !projectUnits.data) return []
  return projectUnits.data.filter(u => u.project === lead.doc.project)
})

// ─── Document ──────────────────────────────────────────────────────────────────
const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const leadStatuses = computed(() => {
  const statuses = statusOptions('lead')
  if (!lead.doc.status) lead.doc.status = statuses?.[0]?.value
  return statuses
})

// ─── Remote resources — Link fields only ──────────────────────────────────────
// Select field options come from OPT (parsed from embedded JSON), NOT from API calls.

const salutations = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Salutation', fields: ['name'], limit_page_length: 50, order_by: 'name asc' },
  auto: true,
})
const leadSources = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'CRM Lead Source', fields: ['name'], limit_page_length: 100, order_by: 'name asc' },
  auto: true,
})
const territories = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'CRM Territory', fields: ['name'], limit_page_length: 200, order_by: 'name asc' },
  auto: true,
})
const industries = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'CRM Industry', fields: ['name'], limit_page_length: 200, order_by: 'name asc' },
  auto: true,
})
const projects = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Real Estate Project', fields: ['name', 'project_name'], limit_page_length: 999, order_by: 'project_name asc' },
  auto: true,
})
const projectUnits = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Project Unit', fields: ['name', 'unit_name', 'project'], limit_page_length: 999, order_by: 'unit_name asc' },
  auto: true,
})
const units = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Unit', fields: ['name', 'unit_name'], limit_page_length: 999, order_by: 'unit_name asc' },
  auto: true,
})

// ─── Create Lead ──────────────────────────────────────────────────────────────
const createLead = createResource({ url: 'frappe.client.insert' })

async function createNewLead() {
  await triggerOnBeforeCreate?.()

  createLead.submit(
    { doc: { doctype: 'CRM Lead', ...lead.doc } },
    {
      validate() {
        error.value      = null
        fieldError.value = null

        if (!lead.doc.first_name) {
          fieldError.value = 'first_name'
          error.value = __('First Name is mandatory')
          return error.value
        }
        if (!lead.doc.mobile_no) {
          fieldError.value = 'mobile_no'
          error.value = __('Mobile No is mandatory')
          return error.value
        }
        if (isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))) {
          fieldError.value = 'mobile_no'
          error.value = __('Mobile No must be a valid number')
          return error.value
        }
        if (lead.doc.email && !lead.doc.email.includes('@')) {
          fieldError.value = 'email'
          error.value = __('Invalid Email address')
          return error.value
        }
        if (!lead.doc.status) {
          error.value = __('Status is required')
          return error.value
        }
        if (lead.doc.property_year_built &&
          (lead.doc.property_year_built < 1900 || lead.doc.property_year_built > currentYear)) {
          error.value = __(`Year Built must be between 1900 and ${currentYear}`)
          return error.value
        }
        if (lead.doc.property_min_price && lead.doc.property_max_price &&
          lead.doc.property_min_price > lead.doc.property_max_price) {
          error.value = __('Min Budget cannot exceed Max Budget')
          return error.value
        }
        if (lead.doc.property_down_payment != null &&
          (lead.doc.property_down_payment < 0 || lead.doc.property_down_payment > 100)) {
          error.value = __('Down Payment must be between 0% and 100%')
          return error.value
        }

        isLeadCreating.value = true
      },
      onSuccess(data) {
        capture('lead_created')
        isLeadCreating.value = false
        show.value = false
        router.push({ name: 'Lead', params: { leadId: data.name } })
        updateOnboardingStep('create_first_lead', true, false, () => {
          localStorage.setItem('firstLead' + user, data.name)
        })
      },
      onError(err) {
        isLeadCreating.value = false
        error.value = err.messages ? err.messages.join('\n') : err.message
      },
    },
  )
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  lead.doc = {
    no_of_employees:    OPT.no_of_employees[0],
    property_min_price: 0,
    property_max_price: 0,
    property_space:     0,
  }
  Object.assign(lead.doc, props.defaults)
  if (!lead.doc?.lead_owner) lead.doc.lead_owner = getUser().name
  if (!lead.doc?.status && leadStatuses.value[0]?.value) {
    lead.doc.status = leadStatuses.value[0].value
  }
})
</script>

<style scoped>
.fi {
  @apply w-full h-10 bg-white border border-gray-200 rounded-lg px-3 text-sm text-gray-700
         focus:outline-none focus:border-[#4A90E2] focus:ring-2 focus:ring-[#4A90E2]/10
         transition-colors placeholder-gray-300;
}
.select-fi {
  @apply appearance-none cursor-pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 2rem;
}
</style>