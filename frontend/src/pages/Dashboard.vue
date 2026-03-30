<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
      <template #right-header>
        <Button v-if="!editing" :label="__('Refresh')" :iconLeft="LucideRefreshCcw" @click="reloadAll" />
        <Button v-if="!editing && isAdmin()" :label="__('Edit')" :iconLeft="LucidePenLine" @click="enableEditing" />
        <Button v-if="editing" :label="__('Chart')" iconLeft="plus" @click="showAddChartModal = true" />
        <Button v-if="editing && isAdmin()" :label="__('Reset to default')" :iconLeft="LucideUndo2" @click="resetToDefault" />
        <Button v-if="editing" :label="__('Cancel')" @click="cancel" />
        <Button v-if="editing" variant="solid" :label="__('Save')" :disabled="!dirty" :loading="saveDashboard.loading" @click="save" />
      </template>
    </LayoutHeader>

    <!-- Filters -->
    <div class="p-4 pb-2 flex flex-wrap items-center gap-3 bg-white border-b border-gray-100">
      <Dropdown
        v-if="!showDatePicker"
        :options="dropdownOptions"
        v-model="preset"
        :placeholder="__('Select Range')"
        :button="{ label: __(preset), variant: 'outline', iconRight: 'chevron-down', iconLeft: 'calendar' }"
        class="!w-full max-w-[180px]"
      />
      <DateRangePicker
        v-else ref="datePickerRef" class="!w-44"
        :value="filters.period" variant="outline" :placeholder="__('Period')"
        @change="onDateRangeChange" :formatter="formatRange"
      >
        <template #prefix><LucideCalendar class="size-4 text-ink-gray-5 mr-2" /></template>
      </DateRangePicker>

      <Link
        v-if="isAdmin() || isManager()"
        class="form-control w-48" variant="outline"
        :value="filters.user && getUser(filters.user).full_name"
        doctype="User"
        :filters="{ name: ['in', users.data.crmUsers?.map((u) => u.name)] }"
        @change="(v) => updateFilter('user', v)"
        :placeholder="__('All Sales Users')" :hideMe="true"
      >
        <template #prefix><UserAvatar v-if="filters.user" class="mr-2" :user="filters.user" size="sm" /></template>
        <template #item-prefix="{ option }"><UserAvatar class="mr-2" :user="option.value" size="sm" /></template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value"><div class="cursor-pointer">{{ getUser(option.value).full_name }}</div></Tooltip>
        </template>
      </Link>
    </div>

    <!-- Body -->
    <div class="w-full overflow-y-auto pb-20">
      <DashboardGrid
        v-if="!dashboardItems.loading && dashboardItems.data && !editing"
        class="pt-4 px-5" v-model="dashboardItems.data" :editing="editing"
      />

      <div v-if="!editing" class="px-5 mt-6 space-y-10">

        <!-- ══════════════════════════════════════════════════════
             SECTION 1: LEADS PERFORMANCE
        ══════════════════════════════════════════════════════ -->
        <section>
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-3">
              <div class="size-10 rounded-xl bg-blue-50 flex items-center justify-center">
                <LucideTarget class="size-5 text-blue-600" />
              </div>
              <div>
                <h2 class="text-lg font-bold text-gray-900">{{ __('Leads Performance') }}</h2>
                <p class="text-xs text-gray-400">{{ preset }}</p>
              </div>
            </div>
            <!-- Search -->
            <div class="relative w-72">
              <input type="text" class="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                :placeholder="__('Search by name or phone...')" v-model="filters.searchText" @input="debouncedLeadSearch" />
              <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
            </div>
          </div>

          <!-- Loading / Error / Empty states -->
          <div v-if="leadsData.loading" class="flex items-center justify-center py-16 text-gray-400">
            <LucideRefreshCcw class="size-5 animate-spin mr-2" /><span>Loading leads...</span>
          </div>
          <div v-else-if="leadsData.error" class="bg-red-50 border border-red-200 p-8 rounded-xl text-center">
            <p class="text-red-600 text-sm mb-3">{{ leadsData.error?.message || leadsData.error }}</p>
            <button @click="leadsData.reload()" class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Retry</button>
          </div>
          <div v-else-if="!leadsData.data?.stats?.total" class="py-16 text-center text-gray-400 border border-dashed border-gray-200 rounded-xl">
            No leads data for this period
          </div>

          <div v-else class="space-y-6">
            <!-- KPI Row -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-blue-50 border border-blue-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-blue-600 flex items-center justify-center"><LucideUsers class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">{{ preset }}</span>
                </div>
                <p class="text-3xl font-black text-blue-900">{{ leadsData.data.stats.total }}</p>
                <p class="text-xs font-semibold text-blue-700 uppercase tracking-wide mt-1">Total Leads</p>
              </div>
              <div class="bg-emerald-50 border border-emerald-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-emerald-600 flex items-center justify-center"><LucideTrendingUp class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">Rate</span>
                </div>
                <!-- FIX: conversionRate is Number, uses monthly_target.won_deals -->
                <p class="text-3xl font-black text-emerald-900">{{ conversionRate }}%</p>
                <p class="text-xs font-semibold text-emerald-700 uppercase tracking-wide mt-1">Conversion Rate</p>
              </div>
              <div class="bg-purple-50 border border-purple-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-purple-600 flex items-center justify-center"><LucideClock class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">Avg</span>
                </div>
                <p class="text-3xl font-black text-purple-900">{{ leadsData.data.conversion?.avg_days || 0 }}</p>
                <p class="text-xs font-semibold text-purple-700 uppercase tracking-wide mt-1">Days to Close</p>
              </div>
              <div class="bg-amber-50 border border-amber-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-amber-600 flex items-center justify-center"><LucideStar class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">Won</span>
                </div>
                <p class="text-3xl font-black text-amber-900">{{ leadsData.data.monthly_target?.won_deals || 0 }}</p>
                <p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mt-1">Closed Deals</p>
              </div>
            </div>

            <!-- Status Funnel + Donut row -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Status funnel — uses real CRM Lead Statuses from DB -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Lead Status Funnel</h3>
                <div v-if="leadsData.data.status_funnel?.length" class="space-y-2">
                  <div v-for="item in leadsData.data.status_funnel" :key="item.status" class="flex items-center gap-3 group">
                    <span class="text-xs font-semibold text-gray-500 w-32 truncate">{{ item.status }}</span>
                    <div class="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div class="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                        :style="{ width: Math.max(item.pct, 2) + '%', backgroundColor: item.color }">
                        <span class="text-[9px] font-black text-white" v-if="item.pct > 10">{{ item.count }}</span>
                      </div>
                    </div>
                    <span class="text-xs font-black text-gray-700 w-8 text-right">{{ item.count }}</span>
                    <span class="text-[10px] text-gray-400 w-10 text-right">{{ item.pct }}%</span>
                  </div>
                </div>
                <div v-else class="py-8 text-center text-sm text-gray-400">No status data</div>
              </div>

              <!-- Pipeline Donut -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-sm font-bold text-gray-900">Pipeline Distribution</h3>
                  <span class="text-xs text-gray-400">{{ leadsData.data.stats.total }} leads</span>
                </div>
                <div class="flex items-center gap-6">
                  <div class="relative size-36 shrink-0" v-if="donutHasData">
                    <svg viewBox="0 0 120 120" class="w-full h-full -rotate-90">
                      <circle cx="60" cy="60" r="46" fill="none" stroke="#f3f4f6" stroke-width="20" />
                      <!-- FIX: correct clockwise offset, colour fallback by index -->
                      <circle v-for="seg in donutSegments" :key="seg.status"
                        cx="60" cy="60" r="46" fill="none"
                        :stroke="seg.color" stroke-width="20"
                        :stroke-dasharray="`${seg.dash} ${seg.gap}`"
                        :stroke-dashoffset="seg.offset"
                        stroke-linecap="butt"
                        class="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-2xl font-black text-gray-900">{{ leadsData.data.monthly_target?.won_deals || 0 }}</span>
                      <span class="text-[9px] font-bold text-gray-400 uppercase">Won</span>
                    </div>
                  </div>
                  <div v-else class="size-36 flex items-center justify-center bg-gray-50 rounded-full border-2 border-dashed border-gray-200">
                    <span class="text-xs text-gray-400">No data</span>
                  </div>
                  <div class="flex-1 grid grid-cols-1 gap-2 overflow-y-auto max-h-36">
                    <div v-for="seg in donutSegments.slice(0,6)" :key="seg.status" class="flex items-center gap-2">
                      <span class="size-2.5 rounded-full shrink-0" :style="{ background: seg.color }"></span>
                      <span class="text-xs text-gray-600 truncate">{{ seg.status }}</span>
                      <span class="text-xs font-bold text-gray-800 ml-auto">{{ seg.count }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Activities + Status Grid -->
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <!-- Activities -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Activity Breakdown</h3>
                <div class="grid grid-cols-2 gap-3">
                  <div v-for="act in activityItems" :key="act.key"
                    class="flex flex-col items-center p-3 rounded-xl border border-gray-100 bg-gray-50 hover:bg-white hover:border-gray-200 transition-all group">
                    <div class="size-9 rounded-lg mb-2 flex items-center justify-center transition-transform group-hover:scale-110" :style="{ background: act.bg }">
                      <component :is="act.icon" class="size-4" :style="{ color: act.color }" />
                    </div>
                    <span class="text-lg font-black text-gray-900">{{ leadsData.data.activities?.[act.key] ?? 0 }}</span>
                    <span class="text-[9px] font-bold text-gray-400 uppercase">{{ act.label }}</span>
                  </div>
                </div>
              </div>

              <!-- Leads by Status cards -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6 xl:col-span-2">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-sm font-bold text-gray-900">Leads by Status</h3>
                  <RouterLink :to="{ name: 'Leads', query: buildLeadQuery() }" class="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
                    View all <LucideArrowRight class="size-3" />
                  </RouterLink>
                </div>
                <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
                  <RouterLink v-for="item in leadOverviewCards" :key="item.status"
                    :to="{ name: 'Leads', query: buildLeadQuery({ status: item.db_status }) }"
                    class="flex flex-col items-center p-3 rounded-xl border border-gray-100 hover:border-blue-200 hover:shadow-sm hover:-translate-y-0.5 transition-all group bg-white">
                    <div class="size-9 rounded-lg mb-2 flex items-center justify-center" :style="{ background: item.bg }">
                      <component :is="item.icon" class="size-5" :style="{ color: item.color }" />
                    </div>
                    <span class="text-xl font-black text-gray-900 group-hover:text-blue-600">{{ item.count }}</span>
                    <span class="text-[9px] font-bold text-gray-400 text-center uppercase mt-0.5 leading-none">{{ __(item.status) }}</span>
                  </RouterLink>
                </div>
              </div>
            </div>

            <!-- Lost Reasons + Sources -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Lost Reasons — FIX: real DB data, no Math.random() -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-5 pb-4 border-b border-gray-100">
                  <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <LucideXCircle class="size-4 text-red-500" /> Lost Reasons
                  </h3>
                  <!-- FIX: conversionRate is Number so subtraction is arithmetic -->
                  <div class="flex gap-3 text-xs text-gray-400">
                    <span class="flex items-center gap-1"><span class="size-2 bg-emerald-400 rounded-full"></span>{{ conversionRate }}% won</span>
                    <span class="flex items-center gap-1"><span class="size-2 bg-red-400 rounded-full"></span>{{ (100 - conversionRate).toFixed(1) }}% lost</span>
                  </div>
                </div>
                <div v-if="lostReasonChartData.length" class="flex items-end gap-3 h-52">
                  <div v-for="item in lostReasonChartData" :key="item.reason"
                    class="flex-1 flex flex-col items-center justify-end h-full group">
                    <span class="text-xs font-bold text-gray-500 mb-1">{{ item.count }}</span>
                    <div class="w-full rounded-t-lg transition-all duration-700 origin-bottom group-hover:scale-x-105"
                      :style="{ height: item.heightPct + '%', backgroundColor: item.color }"></div>
                    <p class="text-[9px] font-semibold text-gray-400 mt-2 text-center uppercase leading-none truncate w-full">{{ item.reason }}</p>
                  </div>
                </div>
                <div v-else class="py-10 text-center text-sm text-gray-400 bg-gray-50 rounded-xl">No lost reasons recorded</div>
              </div>

              <!-- Source Performance — FIX: reads .total & .won, dynamic scale -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-5 pb-4 border-b border-gray-100">
                  <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <LucideBarChartHero class="size-4 text-blue-500" /> Source Performance
                  </h3>
                  <div class="flex gap-3 text-xs text-gray-400">
                    <span class="flex items-center gap-1"><span class="size-2 bg-blue-500 rounded-full"></span>Total</span>
                    <span class="flex items-center gap-1"><span class="size-2 bg-emerald-400 rounded-full"></span>Won</span>
                  </div>
                </div>
                <div v-if="leadSourcesChartData.length" class="flex items-end justify-around gap-4 h-52">
                  <div v-for="item in leadSourcesChartData" :key="item.source"
                    class="flex flex-col items-center justify-end h-full group">
                    <div class="flex gap-1.5 items-end h-full">
                      <div class="w-3 bg-blue-600 rounded-t-full shadow-sm transition-all duration-1000 origin-bottom relative group-hover:bg-blue-500"
                        :style="{ height: item.totalHeight + '%' }">
                        <div class="absolute -top-7 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[9px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap">
                          {{ item.total }}
                        </div>
                      </div>
                      <div class="w-3 bg-emerald-400 rounded-t-full shadow-sm transition-all duration-1000 origin-bottom border border-emerald-100"
                        :style="{ height: item.wonHeight + '%' }"></div>
                    </div>
                    <span class="text-[9px] font-bold text-gray-500 mt-2 text-center uppercase">{{ item.source }}</span>
                  </div>
                </div>
                <div v-else class="py-10 text-center text-sm text-gray-400 bg-gray-50 rounded-xl">No source data</div>
              </div>
            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════════════════
             SECTION 2: Inventory PERFORMANCE
        ══════════════════════════════════════════════════════ -->
        <section class="border-t border-gray-100 pt-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="size-10 rounded-xl bg-indigo-50 flex items-center justify-center">
              <LucideLayoutGrid class="size-5 text-indigo-600" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-gray-900">{{ __('Inventory Performance') }}</h2>
              <p class="text-xs text-gray-400">Live inventory data</p>
            </div>
          </div>

          <div v-if="inventoryData.loading" class="flex items-center justify-center py-16 text-gray-400">
            <LucideRefreshCcw class="size-5 animate-spin mr-2" /><span>Loading inventory...</span>
          </div>
          <div v-else-if="inventoryData.error" class="bg-red-50 border border-red-200 p-8 rounded-xl text-center">
            <p class="text-red-600 text-sm mb-3">{{ inventoryData.error?.message || inventoryData.error }}</p>
            <button @click="inventoryData.reload()" class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Retry</button>
          </div>

          <div v-else class="space-y-6">
            <!-- Overview cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-gradient-to-br from-indigo-50 to-white rounded-2xl p-6 border border-indigo-100">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2"><LucideBuilding2 class="size-5 text-indigo-600" /> Projects</h3>
                  <span class="text-xs font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full">{{ inventoryData.data.project_stats?.total || 0 }}</span>
                </div>
                <div class="grid grid-cols-4 gap-3">
                  <div class="text-center p-3 rounded-xl bg-white border border-gray-100">
                    <p class="text-2xl font-black text-gray-900">{{ inventoryData.data.project_stats?.total || 0 }}</p>
                    <p class="text-[10px] font-semibold text-gray-400 uppercase mt-1">Total</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-blue-50 border border-blue-100">
                    <p class="text-2xl font-black text-blue-600">{{ inventoryData.data.project_stats?.available || 0 }}</p>
                    <p class="text-[10px] font-semibold text-blue-500 uppercase mt-1">Active</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                    <p class="text-2xl font-black text-emerald-600">{{ inventoryData.data.project_stats?.sold || 0 }}</p>
                    <p class="text-[10px] font-semibold text-emerald-500 uppercase mt-1">Sold</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-gray-100 border border-gray-200">
                    <p class="text-2xl font-black text-gray-500">{{ inventoryData.data.project_stats?.archived || 0 }}</p>
                    <p class="text-[10px] font-semibold text-gray-400 uppercase mt-1">Archived</p>
                  </div>
                </div>
              </div>
              <div class="bg-gradient-to-br from-emerald-50 to-white rounded-2xl p-6 border border-emerald-100">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2"><LucideHome class="size-5 text-emerald-600" /> Units</h3>
                  <span class="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">{{ inventoryData.data.unit_stats?.total || 0 }}</span>
                </div>
                <div class="grid grid-cols-4 gap-3">
                  <div class="text-center p-3 rounded-xl bg-white border border-gray-100">
                    <p class="text-2xl font-black text-gray-900">{{ inventoryData.data.unit_stats?.total || 0 }}</p>
                    <p class="text-[10px] font-semibold text-gray-400 uppercase mt-1">Total</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                    <p class="text-2xl font-black text-emerald-600">{{ inventoryData.data.unit_stats?.available || 0 }}</p>
                    <p class="text-[10px] font-semibold text-emerald-500 uppercase mt-1">Available</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-blue-50 border border-blue-100">
                    <p class="text-2xl font-black text-blue-600">{{ inventoryData.data.unit_stats?.sold || 0 }}</p>
                    <p class="text-[10px] font-semibold text-blue-500 uppercase mt-1">Sold</p>
                  </div>
                  <div class="text-center p-3 rounded-xl bg-amber-50 border border-amber-100">
                    <p class="text-2xl font-black text-amber-600">{{ inventoryData.data.unit_stats?.reserved || 0 }}</p>
                    <p class="text-[10px] font-semibold text-amber-500 uppercase mt-1">Reserved</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Insights -->
            <div v-if="inventoryData.data.insights?.length" class="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 class="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
                <LucideLightbulb class="size-5 text-amber-500" /> Key Insights
              </h3>
              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div v-for="ins in inventoryData.data.insights" :key="ins.label"
                  class="p-4 bg-gray-50 rounded-xl border border-gray-100 hover:border-indigo-200 hover:bg-white transition-all">
                  <p class="text-[10px] font-bold text-gray-400 uppercase mb-1">{{ ins.label }}</p>
                  <p class="text-base font-black text-gray-900">{{ ins.value }}</p>
                  <p class="text-[10px] text-gray-400 mt-0.5 italic">{{ ins.sub }}</p>
                </div>
              </div>
            </div>

            <!-- Project donuts -->
            <div v-if="inventoryPerformanceData.length" class="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div v-for="proj in inventoryPerformanceData" :key="proj.project"
                class="bg-white rounded-2xl border border-gray-200 p-5 hover:shadow-lg transition-all">
                <h4 class="text-xs font-bold text-gray-700 uppercase mb-4 pb-3 border-b border-gray-100">{{ proj.project }}</h4>
                <div class="flex items-center gap-4">
                  <div class="relative size-24 shrink-0">
                    <svg viewBox="0 0 100 100" class="size-full -rotate-90">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#f3f4f6" stroke-width="12" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#4f46e5" stroke-width="12"
                        :stroke-dasharray="`${(proj.sold/Math.max(proj.total,1))*251.2} 251.2`"
                        stroke-linecap="round" class="transition-all duration-1000" />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-lg font-black text-gray-900">{{ proj.percent }}%</span>
                      <span class="text-[8px] font-bold text-gray-400 uppercase">Sold</span>
                    </div>
                  </div>
                  <div class="flex-1 space-y-2">
                    <div>
                      <div class="flex items-center gap-1.5 mb-0.5"><div class="size-2 rounded-full bg-indigo-600"></div><span class="text-[10px] font-bold text-gray-600">Sold</span></div>
                      <span class="text-base font-black text-gray-900 pl-3.5">{{ proj.sold }}</span>
                    </div>
                    <div>
                      <div class="flex items-center gap-1.5 mb-0.5"><div class="size-2 rounded-full bg-blue-300"></div><span class="text-[10px] font-bold text-gray-400">Available</span></div>
                      <span class="text-base font-black text-gray-500 pl-3.5">{{ proj.total - proj.sold }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Profits + Reservations -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Profits -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-5">
                  <h3 class="text-sm font-bold text-gray-900">Expected vs Realized Profits</h3>
                  <span class="text-xs text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">{{ currentMonth }}</span>
                </div>
                <div class="flex items-end justify-between gap-4 h-48">
                  <div v-for="(item, idx) in inventoryProfitsData" :key="idx"
                    class="flex-1 flex flex-col items-center justify-end h-full group">
                    <span class="text-sm font-bold mb-2 group-hover:-translate-y-1 transition-transform" :style="{ color: item.color }">{{ item.value || 0 }}K</span>
                    <div class="w-full rounded-t-xl shadow-sm transition-all duration-1000 origin-bottom"
                      :style="{ height: profitBarHeight(item.value) + '%', background: item.color }"></div>
                    <span class="text-xs font-bold text-gray-500 mt-3 uppercase">{{ item.type }}</span>
                  </div>
                </div>
              </div>

              <!-- Reservations — FIX: unit="count", no fake K suffix -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-5">
                  <h3 class="text-sm font-bold text-gray-900">Reservation Status</h3>
                  <span class="text-xs text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">{{ currentMonth }}</span>
                </div>
                <div class="flex items-end justify-between gap-4 h-48">
                  <div v-for="(item, idx) in inventoryReservationsData" :key="idx"
                    class="flex-1 flex flex-col items-center justify-end h-full group">
                    <!-- FIX: display raw count, not "3K" -->
                    <span class="text-sm font-bold mb-2 group-hover:-translate-y-1 transition-transform" :style="{ color: item.color }">{{ item.value || 0 }}</span>
                    <div class="w-full rounded-t-xl shadow-sm transition-all duration-1000 origin-bottom"
                      :style="{ height: reservationBarHeight(item.value) + '%', background: item.color }"></div>
                    <span class="text-xs font-bold text-gray-500 mt-3 uppercase">{{ item.type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════════════════
             SECTION 3: TASKS PERFORMANCE (NEW)
        ══════════════════════════════════════════════════════ -->
        <section class="border-t border-gray-100 pt-8 pb-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="size-10 rounded-xl bg-amber-50 flex items-center justify-center">
              <LucideCalendarCheck class="size-5 text-amber-600" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-gray-900">{{ __('Tasks Performance') }}</h2>
              <p class="text-xs text-gray-400">Calls, meetings, showings & more</p>
            </div>
          </div>

          <div v-if="tasksData.loading" class="flex items-center justify-center py-16 text-gray-400">
            <LucideRefreshCcw class="size-5 animate-spin mr-2" /><span>Loading tasks...</span>
          </div>
          <div v-else-if="tasksData.error" class="bg-red-50 border border-red-200 p-8 rounded-xl text-center">
            <p class="text-red-600 text-sm mb-3">{{ tasksData.error?.message || tasksData.error }}</p>
            <button @click="tasksData.reload()" class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Retry</button>
          </div>

          <div v-else class="space-y-6">
            <!-- Task KPIs -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-blue-50 border border-blue-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-blue-600 flex items-center justify-center"><LucideCheckCircle class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">Total</span>
                </div>
                <p class="text-3xl font-black text-blue-900">{{ tasksData.data?.kpis?.total || 0 }}</p>
                <p class="text-xs font-semibold text-blue-700 uppercase tracking-wide mt-1">All Tasks</p>
              </div>
              <div class="bg-emerald-50 border border-emerald-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-emerald-600 flex items-center justify-center"><LucideTrendingUp class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">Rate</span>
                </div>
                <p class="text-3xl font-black text-emerald-900">{{ tasksData.data?.kpis?.completion_rate || 0 }}%</p>
                <p class="text-xs font-semibold text-emerald-700 uppercase tracking-wide mt-1">Completion Rate</p>
              </div>
              <div class="bg-red-50 border border-red-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-red-500 flex items-center justify-center"><LucideAlertCircle class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded-full">Alert</span>
                </div>
                <p class="text-3xl font-black text-red-900">{{ tasksData.data?.kpis?.late || 0 }}</p>
                <p class="text-xs font-semibold text-red-700 uppercase tracking-wide mt-1">Overdue Tasks</p>
              </div>
              <div class="bg-purple-50 border border-purple-100 rounded-2xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="size-8 rounded-lg bg-purple-600 flex items-center justify-center"><LucideClock class="size-4 text-white" /></div>
                  <span class="text-xs font-semibold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">Active</span>
                </div>
                <p class="text-3xl font-black text-purple-900">{{ tasksData.data?.kpis?.in_progress || 0 }}</p>
                <p class="text-xs font-semibold text-purple-700 uppercase tracking-wide mt-1">In Progress</p>
              </div>
            </div>

            <!-- Status + Type + Priority -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <!-- Status breakdown -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 class="text-sm font-bold text-gray-900 mb-4">By Status</h3>
                <div class="space-y-3">
                  <div v-for="item in tasksData.data?.status_breakdown || []" :key="item.status"
                    class="flex items-center gap-3">
                    <span class="size-2.5 rounded-full shrink-0" :style="{ background: item.color }"></span>
                    <span class="text-xs text-gray-600 flex-1">{{ item.status }}</span>
                    <div class="w-20 bg-gray-100 rounded-full h-1.5">
                      <div class="h-full rounded-full" :style="{ width: item.pct + '%', backgroundColor: item.color }"></div>
                    </div>
                    <span class="text-xs font-bold text-gray-700 w-8 text-right">{{ item.count }}</span>
                  </div>
                </div>
              </div>

              <!-- Task type breakdown -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 class="text-sm font-bold text-gray-900 mb-4">By Task Type</h3>
                <div class="space-y-3">
                  <div v-for="item in tasksData.data?.type_breakdown || []" :key="item.type"
                    class="flex items-center gap-3">
                    <span class="size-2.5 rounded-full shrink-0" :style="{ background: item.color }"></span>
                    <span class="text-xs text-gray-600 flex-1 capitalize">{{ item.type }}</span>
                    <div class="w-20 bg-gray-100 rounded-full h-1.5">
                      <div class="h-full rounded-full" :style="{ width: item.pct + '%', backgroundColor: item.color }"></div>
                    </div>
                    <span class="text-xs font-bold text-gray-700 w-8 text-right">{{ item.count }}</span>
                  </div>
                </div>
              </div>

              <!-- Priority breakdown -->
              <div class="bg-white rounded-2xl border border-gray-200 p-6">
                <h3 class="text-sm font-bold text-gray-900 mb-4">By Priority</h3>
                <div class="space-y-3 mb-4">
                  <div v-for="item in tasksData.data?.priority_breakdown || []" :key="item.priority"
                    class="flex items-center gap-3">
                    <span class="size-2.5 rounded-full shrink-0" :style="{ background: item.color }"></span>
                    <span class="text-xs text-gray-600 flex-1">{{ item.priority }}</span>
                    <div class="w-20 bg-gray-100 rounded-full h-1.5">
                      <div class="h-full rounded-full" :style="{ width: item.pct + '%', backgroundColor: item.color }"></div>
                    </div>
                    <span class="text-xs font-bold text-gray-700 w-8 text-right">{{ item.count }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Task type performance table -->
            <div class="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Task Type Performance</h3>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-gray-100">
                      <th class="text-left text-[10px] font-bold text-gray-400 uppercase pb-3 pr-4">Type</th>
                      <th class="text-right text-[10px] font-bold text-gray-400 uppercase pb-3 px-4">Total</th>
                      <th class="text-right text-[10px] font-bold text-gray-400 uppercase pb-3 px-4">Done</th>
                      <th class="text-right text-[10px] font-bold text-gray-400 uppercase pb-3 px-4">Late</th>
                      <th class="text-right text-[10px] font-bold text-gray-400 uppercase pb-3 pl-4">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in tasksData.data?.type_performance || []" :key="item.type"
                      class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td class="py-3 pr-4">
                        <div class="flex items-center gap-2">
                          <span class="size-2 rounded-full" :style="{ background: item.color }"></span>
                          <span class="text-xs text-gray-700 capitalize">{{ item.type }}</span>
                        </div>
                      </td>
                      <td class="text-right text-xs font-semibold text-gray-700 px-4">{{ item.total }}</td>
                      <td class="text-right text-xs font-semibold text-emerald-600 px-4">{{ item.done }}</td>
                      <td class="text-right text-xs font-semibold text-red-500 px-4">{{ item.late }}</td>
                      <td class="text-right pl-4">
                        <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                          :class="item.completion_rate >= 70 ? 'bg-emerald-50 text-emerald-700' : item.completion_rate >= 40 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'">
                          {{ item.completion_rate }}%
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Completion by user -->
            <div v-if="tasksData.data?.completion_by_user?.length" class="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 class="text-sm font-bold text-gray-900 mb-4">Completion by Team Member</h3>
              <div class="space-y-3">
                <div v-for="item in tasksData.data.completion_by_user" :key="item.user"
                  class="flex items-center gap-4">
                  <UserAvatar :user="item.user" size="sm" class="shrink-0" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-xs font-semibold text-gray-700 truncate">{{ item.name }}</span>
                      <span class="text-xs font-bold ml-2"
                        :class="item.completion_rate >= 70 ? 'text-emerald-600' : item.completion_rate >= 40 ? 'text-amber-600' : 'text-red-500'">
                        {{ item.completion_rate }}%
                      </span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                      <div class="h-full rounded-full transition-all duration-700"
                        :class="item.completion_rate >= 70 ? 'bg-emerald-500' : item.completion_rate >= 40 ? 'bg-amber-400' : 'bg-red-400'"
                        :style="{ width: item.completion_rate + '%' }"></div>
                    </div>
                  </div>
                  <div class="flex gap-3 text-[10px] text-gray-400 shrink-0">
                    <span class="flex items-center gap-1"><span class="size-1.5 rounded-full bg-emerald-400"></span>{{ item.done }}</span>
                    <span class="flex items-center gap-1"><span class="size-1.5 rounded-full bg-red-400"></span>{{ item.late }}</span>
                    <span class="font-semibold text-gray-600">/ {{ item.total }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>

  <AddChartModal v-if="showAddChartModal" v-model="showAddChartModal" v-model:items="dashboardItems.data" />
</template>

<script setup lang="ts">
import AddChartModal from '@/components/Dashboard/AddChartModal.vue'
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'

import LucideRefreshCcw   from '~icons/lucide/refresh-ccw'
import LucideUndo2        from '~icons/lucide/undo-2'
import LucidePenLine      from '~icons/lucide/pen-line'
import LucideCalendar     from '~icons/lucide/calendar'
import LucideUsers        from '~icons/lucide/users'
import LucideActivity     from '~icons/lucide/activity'
import LucideClock        from '~icons/lucide/clock'
import LucideTrendingUp   from '~icons/lucide/trending-up'
import LucideTarget       from '~icons/lucide/target'
import LucideXCircle      from '~icons/lucide/x-circle'
import LucideGlobe        from '~icons/lucide/globe'
import LucideSearch       from '~icons/lucide/search'
import LucideArrowRight   from '~icons/lucide/arrow-right'
import LucideBarChartHero from '~icons/lucide/bar-chart-2'
import LucidePhone        from '~icons/lucide/phone'
import LucidePhoneForwarded from '~icons/lucide/phone-forwarded'
import LucideMessageSquare  from '~icons/lucide/message-square'
import LucideMessageCircle  from '~icons/lucide/message-circle'
import LucideMail           from '~icons/lucide/mail'
import LucideCalendarCheck  from '~icons/lucide/calendar-check'
import LucideEye            from '~icons/lucide/eye'
import LucideBookmark       from '~icons/lucide/bookmark'
import LucideStar           from '~icons/lucide/star'
import LucideCheckCircle    from '~icons/lucide/check-circle'
import LucideAlertCircle    from '~icons/lucide/alert-circle'
import LucideLayoutGrid     from '~icons/lucide/layout-grid'
import LucideThumbsDown     from '~icons/lucide/thumbs-down'
import LucideBriefcase      from '~icons/lucide/briefcase'
import LucideBuilding2      from '~icons/lucide/building-2'
import LucideHome           from '~icons/lucide/home'
import LucideLightbulb      from '~icons/lucide/lightbulb'
import LucideChevronDown    from '~icons/lucide/chevron-down'

import { usersStore } from '@/stores/users'
import { copy } from '@/utils'
import { getLastXDays, formatter, formatRange } from '@/utils/dashboard'
import { usePageMeta, createResource, DateRangePicker, Dropdown, Tooltip } from 'frappe-ui'
import { ref, reactive, computed, provide, onUnmounted } from 'vue'

const { users, getUser, isManager, isAdmin } = usersStore()

const editing = ref(false)
const showDatePicker = ref(false)
const datePickerRef = ref<any>(null)
const preset = ref('Last 30 Days')
const showAddChartModal = ref(false)

type FilterKey = 'period' | 'user' | 'project' | 'status' | 'searchText'
const filters = reactive<Record<FilterKey, any>>({
  period: getLastXDays(),
  user: null,
  project: null,
  status: null,
  searchText: '',
})

const fromDate = computed(() => filters.period?.split(',')[0] ?? null)
const toDate   = computed(() => filters.period?.split(',')[1] ?? null)
const currentMonth = computed(() => new Date().toLocaleString('default', { month: 'long' }))

// ── Reload helpers ────────────────────────────────────────────────────────────

function reloadAll() {
  dashboardItems.reload()
  leadsData.reload()
  inventoryData.reload()
  tasksData.reload()
}

function reloadLeads() {
  leadsData.reload()
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
function debouncedLeadSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(reloadLeads, 500)
}
onUnmounted(() => { if (searchTimeout) clearTimeout(searchTimeout) })

function updateFilter(key: FilterKey, value: any, callback?: () => void) {
  filters[key] = value
  callback?.()
  reloadAll()
}

function onDateRangeChange(v: string | null) {
  if (!v) {
    showDatePicker.value = false
    filters.period = getLastXDays()
    preset.value = 'Last 30 Days'
  } else {
    filters.period = v
    preset.value = formatter(v)
    showDatePicker.value = false
  }
  reloadAll()
}

const dropdownOptions = computed(() => [
  {
    group: 'Presets', hideLabel: true,
    items: [7, 30, 60, 90].map((days) => ({
      label: `Last ${days} Days`,
      onClick: () => { preset.value = `Last ${days} Days`; filters.period = getLastXDays(days); reloadAll() },
    })),
  },
  {
    label: 'Custom Range',
    onClick: () => { showDatePicker.value = true; preset.value = 'Custom Range'; setTimeout(() => datePickerRef.value?.open(), 0) },
  },
])

// ── Resources ──────────────────────────────────────────────────────────────────

const dashboardItems = createResource({
  url: 'crm.api.dashboard.get_dashboard',
  makeParams() { return { from_date: fromDate.value, to_date: toDate.value, user: filters.user } },
  auto: true,
})

const leadsData = createResource({
  url: 'crm.api.dashboard.get_leads_dashboard',
  makeParams() {
    return { from_date: fromDate.value, to_date: toDate.value, user: filters.user, project: filters.project, status: filters.status, search: filters.searchText }
  },
  auto: true,
})

const inventoryData = createResource({
  url: 'crm.api.dashboard.get_inventory_dashboard',
  makeParams() { return { from_date: fromDate.value, to_date: toDate.value, user: filters.user, project: filters.project } },
  auto: true,
})

const tasksData = createResource({
  url: 'crm.api.dashboard.get_tasks_dashboard',
  makeParams() { return { from_date: fromDate.value, to_date: toDate.value, user: filters.user, project: filters.project } },
  auto: true,
})

// ── Editing ────────────────────────────────────────────────────────────────────

const oldItems = ref<any[]>([])
const dirty = computed(() => editing.value && JSON.stringify(dashboardItems.data) !== JSON.stringify(oldItems.value))

provide('fromDate', fromDate)
provide('toDate', toDate)
provide('filters', filters)

function enableEditing() { editing.value = true; oldItems.value = copy(dashboardItems.data) }
function cancel()        { editing.value = false; dashboardItems.data = copy(oldItems.value) }

const saveDashboard = createResource({
  url: 'frappe.client.set_value', method: 'POST',
  onSuccess: () => { dashboardItems.reload(); editing.value = false },
})

function save() {
  const items = copy(dashboardItems.data)
  items.forEach((item: any) => { delete item.data })
  saveDashboard.submit({ doctype: 'CRM Dashboard', name: 'Manager Dashboard', fieldname: 'layout', value: JSON.stringify(items) })
}

function resetToDefault() {
  createResource({ url: 'crm.api.dashboard.reset_to_default', auto: true, onSuccess: () => { dashboardItems.reload(); editing.value = false } })
}

// ── Leads computed ─────────────────────────────────────────────────────────────

// FIX: returns Number; uses monthly_target.won_deals (not stats.items search)
const conversionRate = computed<number>(() => {
  const stats = leadsData.data?.stats
  if (!stats || stats.total === 0) return 0
  const won = leadsData.data?.monthly_target?.won_deals ?? 0
  return parseFloat(((won / stats.total) * 100).toFixed(1))
})

const FALLBACK_COLOURS = ['#60a5fa','#34d399','#f472b6','#a78bfa','#fb923c','#38bdf8','#4ade80','#e879f9','#facc15','#94a3b8']
const CIRCUMFERENCE = 2 * Math.PI * 46

const donutHasData = computed(() => (leadsData.data?.stats?.total ?? 0) > 0)

// FIX: correct clockwise offset; colour fallback by index
const donutSegments = computed(() => {
  const stats = leadsData.data?.stats
  if (!stats || stats.total === 0) return []
  let cumulative = 0
  return stats.items.map((item: any, idx: number) => {
    const fraction = item.count / stats.total
    const dash = fraction * CIRCUMFERENCE
    const gap  = CIRCUMFERENCE - dash
    const offset = CIRCUMFERENCE * (1 - cumulative)
    cumulative += fraction
    return { ...item, dash, gap, offset, color: item.color || FALLBACK_COLOURS[idx % FALLBACK_COLOURS.length] }
  })
})

// FIX: activity keys aligned to API fields (viewings + bookings added)
const activityItems = [
  { key: 'feedback', label: 'Feedback', icon: LucideMessageSquare, color: '#A855F7', bg: '#F3E8FF' },
  //{ key: 'calls',    label: 'Calls',    icon: LucidePhone,          color: '#6B7280', bg: '#F3F4F6' },
  //{ key: 'email',    label: 'Email',    icon: LucideMail,           color: '#F59E0B', bg: '#FEF3C7' },
  { key: 'whatsapp', label: 'WhatsApp', icon: LucideMessageCircle,  color: '#10B981', bg: '#D1FAE5' },
  //{ key: 'meetings', label: 'Meetings', icon: LucideCalendarCheck,  color: '#06B6D4', bg: '#CFFAFE' },
  //{ key: 'viewings', label: 'Viewings', icon: LucideEye,            color: '#f43f5e', bg: '#fff1f2' },
  //{ key: 'bookings', label: 'Bookings', icon: LucideBookmark,       color: '#0891b2', bg: '#ecfeff' },
  //{ key: 'website',  label: 'Website',  icon: LucideGlobe,          color: '#3B82F6', bg: '#DBEAFE' },
]

const leadOverviewCards = computed(() => {
  const stats = leadsData.data?.stats?.items || []
  const getCount = (s: string) => stats.find((i: any) => i.status === s)?.count ?? 0
  // Real statuses from CRM Lead Status screenshot: New, Contacted, Nurture, Qualified, Unqualified, Junk, Meeting, Follow Up To Meeting
  return [
    { status: 'New',                  db_status: 'New',                  icon: LucideTarget,         color: '#10b981', bg: '#ecfdf5', count: getCount('New') },
    { status: 'Contacted',            db_status: 'Contacted',            icon: LucidePhoneForwarded, color: '#6366f1', bg: '#eef2ff', count: getCount('Contacted') },
    { status: 'Nurture',              db_status: 'Nurture',              icon: LucideActivity,       color: '#3b82f6', bg: '#eff6ff', count: getCount('Nurture') },
    { status: 'Qualified',            db_status: 'Qualified',            icon: LucideCheckCircle,    color: '#8b5cf6', bg: '#f5f3ff', count: getCount('Qualified') },
    { status: 'Unqualified',          db_status: 'Unqualified',          icon: LucideThumbsDown,     color: '#6b7280', bg: '#f3f4f6', count: getCount('Unqualified') },
    { status: 'Junk',                 db_status: 'Junk',                 icon: LucideXCircle,        color: '#ef4444', bg: '#fef2f2', count: getCount('Junk') },
    { status: 'Meeting',              db_status: 'Meeting',              icon: LucideCalendarCheck,  color: '#ec4899', bg: '#fdf2f8', count: getCount('Meeting') },
    { status: 'Follow Up To Meeting', db_status: 'Follow Up To Meeting', icon: LucideClock,          color: '#f59e0b', bg: '#fffbeb', count: getCount('Follow Up To Meeting') },
    { status: 'Reserved',              db_status: 'Reserved',              icon: LucideBookmark,       color: '#0891b2', bg: '#ecfeff', count: getCount('Reserved') } 
   ]
})

// FIX: lost reasons use real DB data — NO Math.random()
const LOST_COLOURS = ['#93c5fd','#6ee7b7','#1f2937','#60a5fa','#a78bfa','#fb923c','#f472b6','#38bdf8','#4ade80','#facc15']

const lostReasonChartData = computed(() => {
  const rs: any[] = leadsData.data?.lost_reasons || []
  if (!rs.length) return []
  const maxCount = Math.max(...rs.map((r: any) => r.count ?? 0), 1)
  return rs.map((r: any, i: number) => ({
    reason:    r.reason,
    count:     r.count ?? 0,
    color:     LOST_COLOURS[i % LOST_COLOURS.length],
    // FIX: data-relative height, no magic constants
    heightPct: Math.min(Math.max(((r.count ?? 0) / maxCount) * 85, (r.count ?? 0) > 0 ? 12 : 4), 85),
  }))
})

// FIX: reads .total and .won (correct API field names), data-relative scale
const leadSourcesChartData = computed(() => {
  const sources: any[] = leadsData.data?.source_chart || []
  if (!sources.length) return []
  const maxTotal = Math.max(...sources.map((s: any) => s.total ?? 0), 1)
  return sources.map((s: any) => ({
    source:      s.source,
    total:       s.total ?? 0,
    won:         s.won   ?? 0,
    totalHeight: (s.total ?? 0) > 0 ? Math.min(Math.max(((s.total ?? 0) / maxTotal) * 80, 10), 90) : 5,
    wonHeight:   (s.won   ?? 0) > 0 ? Math.min(Math.max(((s.won   ?? 0) / maxTotal) * 80,  8), 80) : 3,
  }))
})

// ── Inventory computed ────────────────────────────────────────────────────────

const inventoryPerformanceData = computed(() => inventoryData.data?.performance || [])

const inventoryProfitsData = computed(() => inventoryData.data?.profits || [
  { type: 'Expected', value: 0, color: '#86efac' },
  { type: 'Realized', value: 0, color: '#93c5fd' },
  { type: 'Difference', value: 0, color: '#c084fc' },
])

const inventoryReservationsData = computed(() => inventoryData.data?.reservations || [
  { type: 'Current', value: 0, color: '#3b82f6' },
  { type: 'Completed', value: 0, color: '#10b981' },
  { type: 'Cancelled', value: 0, color: '#ef4444' },
])

// FIX: profits use data-relative bar heights (K values), reservations use count-relative
const profitMax = computed(() => Math.max(...inventoryProfitsData.value.map((d: any) => d.value || 0), 1))
const reservMax = computed(() => Math.max(...inventoryReservationsData.value.map((d: any) => d.value || 0), 1))

const profitBarHeight     = (v: number) => v > 0 ? Math.max((v / profitMax.value) * 80, 8) : 4
const reservationBarHeight = (v: number) => v > 0 ? Math.max((v / reservMax.value) * 80, 8) : 4

// ── Utilities ──────────────────────────────────────────────────────────────────

function buildLeadQuery(extra: Record<string, string> = {}) {
  const q: Record<string, string> = { ...extra }
  if (filters.user) q.user = filters.user
  return q
}

usePageMeta(() => ({ title: __('CRM Dashboard') }))
</script>