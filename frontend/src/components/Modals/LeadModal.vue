<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <!-- Main Container -->
      <div class="flex flex-col items-end p-6 gap-10 bg-white border border-[#DCDCDC] rounded-lg max-h-[90vh] overflow-y-auto">
        
        <!-- Header -->
        <div class="flex flex-row justify-between items-center w-full bg-white">
          <h3 class="font-inter font-semibold text-2xl leading-8 tracking-[-0.005em] text-[#5C5C5C]">
            {{ __('Add New Lead') }}
          </h3>
          
          <!-- Close Button -->
          <button 
            @click="show = false"
            class="w-[37.32px] h-[37.32px] flex items-center justify-center bg-[#4A90E2] rounded-full flex-shrink-0 hover:bg-[#3B7DCC] transition-colors"
          >
            <span class="font-inter font-semibold text-[19.34px] leading-[26px] tracking-[-0.005em] text-[#F7F8FA]">
              ×
            </span>
          </button>
        </div>

        <!-- Lead Information Section -->
        <div class="w-full border border-[#DCDCDC] rounded-lg relative pt-12 pb-6 px-4">
          <!-- Section Header -->
          <div class="absolute -top-[18px] left-4 flex flex-row justify-center items-center px-2 gap-4 bg-white z-10">
            <h3 class="font-inter font-semibold text-2xl leading-8 tracking-[-0.005em] text-[#7D8592]">
              {{ __('Lead Information') }}
            </h3>
          </div>

          <div class="flex flex-col gap-6">
            <!-- Location Row -->
            <div class="w-full">
              <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592] block mb-2">
                {{ __('Location') }}
              </label>
              <div class="flex flex-wrap gap-4">
                <select v-model="lead.doc.city" class="flex-1 min-w-[150px] h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 font-inter text-sm text-[#424242]">
                  <option value="">{{ __('Select City') }}</option>
                  <option value="Cairo">Cairo</option>
                  <option value="New Cairo">New Cairo</option>
                </select>
                <select v-model="lead.doc.state" class="flex-1 min-w-[150px] h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 font-inter text-sm text-[#424242]">
                  <option value="">{{ __('Select Region') }}</option>
                </select>
              </div>
            </div>

            <!-- Form Fields Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <!-- Column 1 -->
              <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Title') }}
                  </label>
                  <input 
                    v-model="lead.doc.salutation"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>
                
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Full Name') }} *
                  </label>
                  <input 
                    v-model="lead.doc.first_name"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>

                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Email') }}
                  </label>
                  <input 
                    v-model="lead.doc.email"
                    type="email"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>
              </div>

              <!-- Column 2 -->
              <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Phone Number') }} *
                  </label>
                  <input 
                    v-model="lead.doc.mobile_no"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>
                
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Other Phone Number') }}
                  </label>
                  <input 
                    v-model="lead.doc.phone"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>

                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Source') }}
                  </label>
                  <input 
                    v-model="lead.doc.source"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>
              </div>

              <!-- Column 3 -->
              <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Campaign') }}
                  </label>
                  <input 
                    v-model="lead.doc.campaign_name"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                  />
                </div>
                
                <div class="flex flex-col gap-1">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Lead Owner') }}
                  </label>
                  <input 
                    v-model="lead.doc.lead_owner"
                    type="text"
                    class="w-full h-12 bg-white border border-[#D8E0F0] shadow-[0px_1px_2px_rgba(184,200,224,0.22)] rounded-lg px-3"
                    disabled
                  />
                </div>

                <div class="flex flex-col gap-2">
                  <label class="font-inter font-semibold text-sm leading-[22px] text-[#7D8592]">
                    {{ __('Lead Origin') }}
                  </label>
                  <div class="flex gap-4 flex-wrap">
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input v-model="lead.doc.lead_type" value="Out Source" type="radio" name="origin" class="w-4 h-4" />
                      <span class="font-heebo text-[13px] leading-[22px] text-[#19212B]">{{ __('Out Source') }}</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input v-model="lead.doc.lead_type" value="Company" type="radio" name="origin" class="w-4 h-4" />
                      <span class="font-heebo text-[13px] leading-[22px] text-[#19212B]">{{ __('Company') }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Property Preference Section -->
        <div class="w-full flex flex-col lg:flex-row gap-6 p-6 bg-white border border-[#DCDCDC] rounded-lg relative pt-12">
          <!-- Section Header -->
          <div class="absolute -top-4 left-4 flex items-center px-2 gap-4 bg-white z-10">
            <h3 class="font-inter font-semibold text-2xl leading-8 tracking-[-0.005em] text-[#7D8592]">
              {{ __('Property Preference') }}
            </h3>
          </div>

          <!-- Core Preference Card -->
          <div class="flex-1 min-w-[250px] border border-[#DCDCDC] rounded-lg p-6 flex flex-col gap-4">
            <div class="flex flex-col gap-2">
              <h4 class="font-inter text-xl leading-7 text-[#7D8592]">{{ __('Core Preference') }}</h4>
              <div class="w-[156px] h-px border-t border-[#DCDCDC]"></div>
            </div>

            <div class="flex flex-col gap-4">
              <!-- Location -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Location') }}
                </label>
                <select v-model="propertyPrefs.city" class="w-full h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 text-sm mb-2">
                  <option value="">{{ __('Select City') }}</option>
                  <option value="Cairo">Cairo</option>
                  <option value="New Cairo">New Cairo</option>
                </select>
                <select v-model="propertyPrefs.region" class="w-full h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 text-sm">
                  <option value="">{{ __('Select Region') }}</option>
                </select>
              </div>

              <!-- Property Type -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Property Type') }}
                </label>
                <div class="flex flex-col gap-2">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.type" value="Residential" type="radio" name="propertyType" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Residential') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.type" value="Commercial" type="radio" name="propertyType" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Commercial') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.type" value="Land" type="radio" name="propertyType" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Land') }}</span>
                  </label>
                  <select v-model="propertyPrefs.subtype" class="w-full h-10 bg-[#BFBFBF] border border-[#E0E0E0] rounded px-2.5 text-sm text-[#7D8592]">
                    <option value="">{{ __('Choose Type') }}</option>
                  </select>
                </div>
              </div>

              <!-- Space Range -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Space') }}
                </label>
                <div class="relative mb-4">
                  <div 
                    @click="handleSpaceSlider"
                    class="w-full h-[21px] bg-[#D1D1D6] rounded relative cursor-pointer"
                  >
                    <div :style="{width: propertyPrefs.space + '%'}" class="absolute h-2 bg-[#007AFF] border border-[#007AFF] rounded pointer-events-none"></div>
                    <div 
                      :style="{left: propertyPrefs.space + '%'}" 
                      class="absolute w-5 h-5 bg-white border-2 border-[#007AFF] rounded-full -ml-2.5 top-[-2px] shadow-sm cursor-pointer pointer-events-none"
                    ></div>
                  </div>
                  <div :style="{left: propertyPrefs.space + '%'}" class="absolute -top-8 -ml-5 bg-[#2280EF] rounded-lg px-2 py-1 pointer-events-none">
                    <span class="text-white text-[10px]">{{ Math.round(propertyPrefs.space * 5) }}m</span>
                    <div class="absolute bottom-[-2px] left-1/2 -ml-1 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-[#2280EF]"></div>
                  </div>
                </div>
                <div class="flex justify-between gap-3">
                  <div class="flex items-center gap-2 border border-[#8B8B8B] rounded-xl px-2 py-1">
                    <span class="text-[#8B8B8B] text-[9.81px]">0m</span>
                    <div class="w-1 h-px bg-[#8B8B8B]"></div>
                  </div>
                  <div class="flex items-center gap-2 border border-[#8B8B8B] rounded-xl px-2 py-1">
                    <span class="text-[#8B8B8B] text-[9.81px]">500m</span>
                  </div>
                </div>
              </div>

              <!-- Floor -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Floor') }}
                </label>
                <div class="flex flex-col gap-2">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.floor" value="Upper Floors" type="radio" name="floor" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Upper Floors') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.floor" value="Ground Floor" type="radio" name="floor" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Ground Floor') }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Property Details Card -->
          <div class="flex-1 min-w-[250px] border border-[#DCDCDC] rounded-lg p-6 flex flex-col gap-4">
            <div class="flex flex-col gap-2">
              <h4 class="font-inter text-xl leading-7 text-[#7D8592]">{{ __('Property Details') }}</h4>
              <div class="w-[156px] h-px border-t border-[#DCDCDC]"></div>
            </div>

            <div class="flex flex-col gap-4">
              <!-- Condition -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Condition') }}
                </label>
                <div class="flex flex-col gap-2">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.condition" value="New" type="radio" name="condition" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('New') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.condition" value="Renovated" type="radio" name="condition" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Renovated') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.condition" value="Need Repair" type="radio" name="condition" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Need Repair') }}</span>
                  </label>
                </div>
              </div>

              <!-- Decoration Status -->
              <div>
                <input 
                  v-model="propertyPrefs.decoration"
                  type="text"
                  :placeholder="__('Decoration Status')"
                  class="w-full h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 text-sm text-[#5C5C5C]"
                />
              </div>

              <!-- Property Relation -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Property Relation') }}
                </label>
                <div class="flex flex-col gap-2 mb-2">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.relation" value="Stand Alone" type="radio" name="relation" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Stand Alone') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.relation" value="Project" type="radio" name="relation" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Project') }}</span>
                  </label>
                </div>
                <select 
                  v-model="propertyPrefs.project" 
                  :disabled="propertyPrefs.relation !== 'Project'"
                  class="w-full h-10 border border-[#E0E0E0] rounded px-2.5 text-sm"
                  :class="propertyPrefs.relation !== 'Project' ? 'bg-[#BFBFBF] text-[#9E9E9E]' : 'bg-white text-[#5C5C5C]'"
                >
                  <option value="">{{ __('Select Project') }}</option>
                  <option 
                    v-for="project in projects.data" 
                    :key="project.name" 
                    :value="project.name"
                  >
                    {{ project.project_name || project.name }}
                  </option>
                </select>
              </div>

              <!-- Year Built -->
              <div>
                <input 
                  v-model="propertyPrefs.yearBuilt"
                  type="number"
                  :placeholder="__('Year Built')"
                  min="1900"
                  :max="new Date().getFullYear()"
                  class="w-full h-10 bg-white border-[0.3px] border-[#D3D3D3] shadow-[0px_0.5px_4px_rgba(79,79,79,0.08)] rounded px-2.5 text-sm text-[#5C5C5C]"
                />
              </div>

              <!-- Features -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Features') }}
                </label>
                <div class="flex flex-col gap-2">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.features" value="Pool" type="checkbox" class="w-5 h-5 rounded" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Pool') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.features" value="Garage" type="checkbox" class="w-5 h-5 rounded" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Garage') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.features" value="Modern Kitchen" type="checkbox" class="w-5 h-5 rounded" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Modern Kitchen') }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Financial Preference & Notes Column -->
          <div class="flex flex-col gap-6 flex-1 min-w-[250px]">
            <!-- Financial Preference Card -->
            <div class="border border-[#DCDCDC] rounded-lg p-6 flex flex-col gap-4">
              <div class="flex flex-col gap-2">
                <h4 class="font-inter text-xl leading-7 text-[#7D8592]">{{ __('Financial Preference') }}</h4>
                <div class="w-[156px] h-px border-t border-[#DCDCDC]"></div>
              </div>

              <!-- Price Range -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Price') }}
                </label>
                <div class="relative mb-4">
                  <div 
                    @click="handlePriceSlider"
                    class="w-full h-[21px] bg-[#D1D1D6] rounded relative cursor-pointer"
                  >
                    <div :style="{width: propertyPrefs.price + '%'}" class="absolute h-2 bg-[#007AFF] border border-[#007AFF] rounded pointer-events-none"></div>
                    <div 
                      :style="{left: propertyPrefs.price + '%'}" 
                      class="absolute w-5 h-5 bg-white border-2 border-[#007AFF] rounded-full -ml-2.5 top-[-2px] shadow-sm cursor-pointer pointer-events-none"
                    ></div>
                  </div>
                  <div :style="{left: propertyPrefs.price + '%'}" class="absolute -top-8 -ml-5 bg-[#2280EF] rounded-lg px-2 py-1 pointer-events-none">
                    <span class="text-white text-[10px]">${{ Math.round(propertyPrefs.price * 5) }}k</span>
                    <div class="absolute bottom-[-2px] left-1/2 -ml-1 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-[#2280EF]"></div>
                  </div>
                </div>
                <div class="flex justify-between gap-3">
                  <div class="flex items-center gap-2 border border-[#8B8B8B] rounded-xl px-2 py-1">
                    <span class="text-[#8B8B8B] text-[9.81px]">$0</span>
                    <div class="w-1 h-px bg-[#8B8B8B]"></div>
                  </div>
                  <div class="flex items-center gap-2 border border-[#8B8B8B] rounded-xl px-2 py-1">
                    <span class="text-[#8B8B8B] text-[9.81px]">$500k</span>
                  </div>
                </div>
              </div>

              <!-- Payment -->
              <div>
                <label class="font-inter font-medium text-sm leading-[22px] text-[#5C5C5C] block mb-2">
                  {{ __('Payment') }}
                </label>
                <div class="flex gap-6 flex-wrap">
                  <label class="flex items-center gap-1">
                    <input v-model="propertyPrefs.payment" value="Cash" type="radio" name="payment" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Cash') }}</span>
                  </label>
                  <label class="flex items-center gap-1">
                    <input v-model="propertyPrefs.payment" value="Installment" type="radio" name="payment" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Installment') }}</span>
                  </label>
                </div>
              </div>

              <!-- Ownership Type -->
              <div>
                <label class="font-inter font-bold text-sm leading-6 text-[#5C5C5C] block mb-2">
                  {{ __('Ownership Type') }}
                </label>
                <div class="flex gap-6 flex-wrap">
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.ownership" value="Owned" type="radio" name="ownership" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Owned') }}</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="propertyPrefs.ownership" value="Rent" type="radio" name="ownership" class="w-4 h-4" />
                    <span class="font-inter font-medium text-sm text-[#2F2D2D]">{{ __('Rent') }}</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Notes Card -->
            <div class="border border-[#DCDCDC] rounded-lg shadow-[0px_0px_4px_rgba(0,0,0,0.04)] p-4 flex flex-col gap-2 bg-white">
              <div class="flex flex-col gap-2">
                <h4 class="font-inter text-xl leading-7 text-[#7D8592]">{{ __('Notes') }}</h4>
                <textarea 
                  v-model="lead.doc.notes"
                  class="border border-[#DCDCDC] rounded-lg p-2 min-h-[82px] font-inter font-medium text-sm leading-[22px] text-[#2F2D2D] resize-none"
                  :placeholder="__('Enter notes here...')"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-6">
          <button 
            @click="show = false"
            class="flex justify-center items-center px-7 py-2 w-[119px] h-[40px] border border-[#4A90E2] rounded-lg hover:bg-[#F0F7FF] transition-colors"
          >
            <span class="font-inter font-semibold text-[17.9px] leading-[25px] text-[#4A90E2]">
              {{ __('Cancel') }}
            </span>
          </button>
          <button 
            @click="createNewLead"
            :disabled="isLeadCreating"
            class="flex justify-center items-center px-7 py-2 w-[119px] h-[42px] bg-[#4A90E2] border border-[#4A90E2] rounded-lg hover:bg-[#3B7DCC] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="font-inter text-[17.9px] leading-[25px] text-white">
              {{ isLeadCreating ? __('Adding...') : __('Add') }}
            </span>
          </button>
        </div>

        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

// Property Preferences State
const propertyPrefs = ref({
  city: '',
  region: '',
  type: '',
  subtype: '',
  space: 50,
  floor: '',
  condition: '',
  decoration: '',
  relation: '',
  project: '',
  yearBuilt: '',
  features: [],
  price: 50,
  payment: '',
  ownership: ''
})

// Slider handlers
function handleSpaceSlider(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
  propertyPrefs.value.space = percentage
}

function handlePriceSlider(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
  propertyPrefs.value.price = percentage
}

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const leadStatuses = computed(() => {
  let statuses = statusOptions('lead')
  if (!lead.doc.status) {
    lead.doc.status = statuses?.[0]?.value
  }
  return statuses
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Lead'],
  params: { doctype: 'CRM Lead', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = leadStatuses.value
              field.prefix = getLeadStatus(lead.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              lead.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

// Fetch Real Estate Projects
const projects = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Real Estate Project',
    fields: ['name', 'project_name'],
    limit_page_length: 999,
  },
  auto: true,
})

const createLead = createResource({
  url: 'frappe.client.insert',
})

async function createNewLead() {
  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  // Add property preferences to lead doc
  lead.doc.property_city = propertyPrefs.value.city
  lead.doc.property_region = propertyPrefs.value.region
  lead.doc.property_type = propertyPrefs.value.type
  lead.doc.property_subtype = propertyPrefs.value.subtype
  lead.doc.property_space = Math.round(propertyPrefs.value.space * 5)
  lead.doc.property_floor = propertyPrefs.value.floor
  lead.doc.property_condition = propertyPrefs.value.condition
  lead.doc.property_decoration = propertyPrefs.value.decoration
  lead.doc.property_relation = propertyPrefs.value.relation
  lead.doc.property_project = propertyPrefs.value.project
  lead.doc.property_year_built = propertyPrefs.value.yearBuilt ? parseInt(propertyPrefs.value.yearBuilt) : null
  lead.doc.property_features = JSON.stringify(propertyPrefs.value.features)
  lead.doc.property_price_range = Math.round(propertyPrefs.value.price * 5000) // $0 to $500k
  lead.doc.property_payment = propertyPrefs.value.payment
  lead.doc.property_ownership = propertyPrefs.value.ownership

  await triggerOnBeforeCreate?.()

  createLead.submit(
    {
      doc: {
        doctype: 'CRM Lead',
        ...lead.doc,
      },
    },
    {
      validate() {
        error.value = null
        if (!lead.doc.first_name) {
          error.value = __('First Name is mandatory')
          return error.value
        }
        if (!lead.doc.mobile_no) {
          error.value = __('Mobile No is mandatory')
          return error.value
        }
        if (lead.doc.annual_revenue) {
          if (typeof lead.doc.annual_revenue === 'string') {
            lead.doc.annual_revenue = lead.doc.annual_revenue.replace(/,/g, '')
          } else if (isNaN(lead.doc.annual_revenue)) {
            error.value = __('Annual Revenue should be a number')
            return error.value
          }
        }
        if (
          lead.doc.mobile_no &&
          isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))
        ) {
          error.value = __('Mobile No should be a number')
          return error.value
        }
        if (lead.doc.email && !lead.doc.email.includes('@')) {
          error.value = __('Invalid Email')
          return error.value
        }
        if (!lead.doc.status) {
          error.value = __('Status is required')
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
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  lead.doc = { no_of_employees: '1-10' }
  Object.assign(lead.doc, props.defaults)

  if (!lead.doc?.lead_owner) {
    lead.doc.lead_owner = getUser().name
  }
  if (!lead.doc?.status && leadStatuses.value[0]?.value) {
    lead.doc.status = leadStatuses.value[0].value
  }
})
</script>