<template>
  <div
    class="sidebar-root relative flex h-full flex-col"
    :class="isSidebarCollapsed ? 'sidebar-collapsed' : 'sidebar-expanded'"
  >

    <!-- ── Logo / User ── -->
    <div class="sidebar-top">
      <UserDropdown class="p-2" :isCollapsed="isSidebarCollapsed" />
    </div>

    <!-- ── Navigation ── -->
    <div class="sidebar-body scrollbar-hide">

      <!-- Notifications -->
      <div class="nav-section-gap">
        <button
          class="nav-item"
          :class="{ 'nav-item--collapsed': isSidebarCollapsed }"
          @click="toggleNotificationPanel()"
          :title="isSidebarCollapsed ? __('Notifications') : ''"
        >
          <span class="nav-icon">
            <NotificationsIcon class="icon" />
          </span>
          <span v-if="!isSidebarCollapsed" class="nav-label">{{ __('Notifications') }}</span>
          <span v-if="!isSidebarCollapsed && unreadNotificationsCount" class="nav-badge">
            {{ unreadNotificationsCount }}
          </span>
          <span v-if="isSidebarCollapsed && unreadNotificationsCount" class="nav-badge-dot" />
        </button>
      </div>

      <div class="nav-divider" />

      <!-- Main nav links -->
      <div class="nav-section-gap">
        <template v-for="(link, idx) in mainLinks" :key="link.label + idx">

          <!-- Link with sublinks (Leads, Inventory…) -->
          <div v-if="link.views" class="nav-group">
            <div
              class="nav-group-header"
              :class="{ 'nav-group-header--collapsed': isSidebarCollapsed }"
            >
              <!-- Main clickable link -->
              <router-link :to="link.to" custom v-slot="{ navigate, isActive }">
                <button
                  class="nav-item nav-item--main"
                  :class="[
                    { 'nav-item--active': isActive },
                    { 'nav-item--collapsed': isSidebarCollapsed },
                  ]"
                  :title="isSidebarCollapsed ? __(link.label) : ''"
                  @click="navigate"
                >
                  <span class="nav-icon">
                    <component :is="link.icon" class="icon" />
                  </span>
                  <span v-if="!isSidebarCollapsed" class="nav-label">{{ __(link.label) }}</span>
                </button>
              </router-link>

              <!-- Caret — ONLY visible when NOT collapsed -->
              <button
                v-if="!isSidebarCollapsed"
                class="nav-caret"
                :class="{ 'nav-caret--open': openDropdowns[idx] }"
                @click.stop="toggleGroup(idx)"
              >
                <FeatherIcon name="chevron-right" class="h-3 w-3" />
              </button>
            </div>

            <!-- Sublinks — hidden when collapsed -->
            <transition name="submenu">
              <div
                v-if="!isSidebarCollapsed && openDropdowns[idx]"
                class="sublinks"
              >
                <button
                  v-for="(sub, sidx) in link.views"
                  :key="sub.label + sidx"
                  class="sublink"
                  @click="navigateSublink(sub)"
                >
                  <span class="sublink-pip" />
                  <span class="sublink-label">{{ __(sub.label) }}</span>
                </button>
              </div>
            </transition>
          </div>

          <!-- Plain link -->
          <router-link
            v-else
            :to="resolveTo(link.to)"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              class="nav-item"
              :class="[
                { 'nav-item--active': isActive },
                { 'nav-item--collapsed': isSidebarCollapsed },
              ]"
              :title="isSidebarCollapsed ? __(link.label) : ''"
              @click="navigate"
            >
              <span class="nav-icon">
                <component :is="link.icon" class="icon" />
              </span>
              <span v-if="!isSidebarCollapsed" class="nav-label">{{ __(link.label) }}</span>
            </button>
          </router-link>

        </template>
      </div>

      <!-- Public views -->
      <template v-if="getPublicViews().length">
        <div class="nav-divider" />
        <div v-if="!isSidebarCollapsed" class="nav-section-label">{{ __('Public Views') }}</div>
        <div class="nav-section-gap">
          <router-link
            v-for="view in parsedPublicViews"
            :key="view.label"
            :to="view.to"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              class="nav-item"
              :class="[{ 'nav-item--active': isActive }, { 'nav-item--collapsed': isSidebarCollapsed }]"
              :title="isSidebarCollapsed ? view.label : ''"
              @click="navigate"
            >
              <span class="nav-icon"><PinIcon class="icon" /></span>
              <span v-if="!isSidebarCollapsed" class="nav-label">{{ view.label }}</span>
            </button>
          </router-link>
        </div>
      </template>

      <!-- Pinned views -->
      <template v-if="getPinnedViews().length">
        <div class="nav-divider" />
        <div v-if="!isSidebarCollapsed" class="nav-section-label">{{ __('Pinned Views') }}</div>
        <div class="nav-section-gap">
          <router-link
            v-for="view in parsedPinnedViews"
            :key="view.label"
            :to="view.to"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              class="nav-item"
              :class="[{ 'nav-item--active': isActive }, { 'nav-item--collapsed': isSidebarCollapsed }]"
              :title="isSidebarCollapsed ? view.label : ''"
              @click="navigate"
            >
              <span class="nav-icon"><PinIcon class="icon" /></span>
              <span v-if="!isSidebarCollapsed" class="nav-label">{{ view.label }}</span>
            </button>
          </router-link>
        </div>
      </template>

    </div>

    <!-- ── Footer ── -->
    <div class="sidebar-footer">
      <SignupBanner
        v-if="isDemoSite"
        :isSidebarCollapsed="isSidebarCollapsed"
        :afterSignup="() => capture('signup_from_demo_site')"
      />
      <TrialBanner
        v-if="isFCSite"
        :isSidebarCollapsed="isSidebarCollapsed"
        :afterUpgrade="() => capture('upgrade_plan_from_trial_banner')"
      />

      <!-- Collapse toggle -->
      <button
        class="nav-item nav-item--muted"
        :class="{ 'nav-item--collapsed': isSidebarCollapsed }"
        :title="isSidebarCollapsed ? __('Expand sidebar') : ''"
        @click="isSidebarCollapsed = !isSidebarCollapsed"
      >
        <span class="nav-icon">
          <CollapseSidebar
            class="icon transition-transform duration-300"
            :class="{ '[transform:rotateY(180deg)]': isSidebarCollapsed }"
          />
        </span>
        <span v-if="!isSidebarCollapsed" class="nav-label">{{ __('Collapse') }}</span>
      </button>
    </div>

    <Notifications />
    <Settings />

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStorage } from '@vueuse/core'
import { FeatherIcon } from 'frappe-ui'
import { SignupBanner, TrialBanner } from 'frappe-ui/frappe'
import router from '@/router'
import { capture } from '@/telemetry'

// ── Icons ──────────────────────────────────────────────────────────────────
import LucideArchive         from '~icons/lucide/archive'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LeadsIcon             from '@/components/Icons/LeadsIcon.vue'
import ContactsIcon          from '@/components/Icons/ContactsIcon.vue'
import NoteIcon              from '@/components/Icons/NoteIcon.vue'
import TaskIcon              from '@/components/Icons/TaskIcon.vue'
import PinIcon               from '@/components/Icons/PinIcon.vue'
import CollapseSidebar       from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon     from '@/components/Icons/NotificationsIcon.vue'

// ── Components ─────────────────────────────────────────────────────────────
import UserDropdown  from '@/components/UserDropdown.vue'
import Notifications from '@/components/Notifications.vue'
import Settings      from '@/components/Settings/Settings.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
// ── Stores ─────────────────────────────────────────────────────────────────
import { viewsStore }                                    from '@/stores/views'
import { unreadNotificationsCount, notificationsStore }  from '@/stores/notifications'
import { usersStore }                                    from '@/stores/users'

const { getPinnedViews, getPublicViews }   = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()
const { isManager, isSalesUser, users }   = usersStore()

// ── State ──────────────────────────────────────────────────────────────────
const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)
const isFCSite           = ref(window.is_fc_site)
const isDemoSite         = ref(window.is_demo_site)

// Tracks open/closed per group by index
const openDropdowns = reactive({})

function toggleGroup(idx) {
  openDropdowns[idx] = !openDropdowns[idx]
}

// ── Sub-links definitions ──────────────────────────────────────────────────
const leadsSubLinks = [
  { label: 'Create Lead',  action: 'create' },
  { label: 'New',          query: { status: 'New' } },
  { label: 'Follow Up',    query: { status: 'Follow Up' } },
  { label: 'No Answer',    query: { status: 'No Answer' } },
  { label: 'Meeting',      query: { status: 'Meeting' } },
  { label: 'Showing',      query: { status: 'Showing' } },
  { label: 'Visiting',     query: { status: 'Visiting' } },
  { label: 'Qualified',    query: { status: 'Qualified' } },
  { label: 'Unqualified',  query: { status: 'Unqualified' } },
]

const inventorySubLinks = [
  { label: 'Projects', to: { name: 'Inventory', query: { tab: 'projects' } } },
  { label: 'Units',    to: { name: 'Inventory', query: { tab: 'units'     } } },
]

// ── Navigate sublink ───────────────────────────────────────────────────────
function navigateSublink(sub) {
  if (!sub) return
  if (sub.action === 'create') {
    router.push({ name: 'Leads', query: { create: '1', _t: Date.now() } }).catch(() => {})
    return
  }
  if (sub.query) { router.push({ name: 'Leads', query: sub.query }).catch(() => {}); return }
  if (sub.to)    { router.push(sub.to).catch(() => {}); return }
  if (sub.path)  { router.push({ path: sub.path }).catch(() => {}); return }
}

// ── Resolve `to` to always be a route object ──────────────────────────────
function resolveTo(to) {
  if (!to) return '/'
  if (typeof to === 'string') return { name: to }
  return to
}

// ── Main nav links ─────────────────────────────────────────────────────────
const mainLinks = computed(() => {
  const all = [
    {
      label:     'Dashboard',
      icon:      LucideLayoutDashboard,
      to:        { name: 'Dashboard' },
      condition: () => isManager() || isSalesUser(),
    },
    {
      label: 'Leads',
      icon:  LeadsIcon,
      to:    { name: 'Leads' },
      views: leadsSubLinks,
    },
    {
      label: 'Reservations',
      icon:  LucideArchive,
      to:    { name: 'Reservations' },
    },
    {
      label: 'Inventory',
      icon:  LucideArchive,
      to:    { name: 'Inventory' },
      views: inventorySubLinks,
    },
    {
      label: 'Contacts',
      icon:  ContactsIcon,
      to:    { name: 'Contacts' },
    },
    {
      label: 'Notes',
      icon:  NoteIcon,
      to:    { name: 'Notes' },
    },
   // {
 // label: 'Calendar',
  //icon:  CalendarIcon,
  //to:    { name: 'Calendar' },
//},
    
    {
      label: 'Tasks',
      icon:  TaskIcon,
      to:    { name: 'Tasks' },
    },
  ]
  return all.filter(l => (l.condition ? l.condition() : true))
})

// ── Parsed saved/pinned views ──────────────────────────────────────────────
function parseViews(views) {
  return views.map(v => ({
    label: v.label,
    to: {
      name:   v.route_name,
      params: { viewType: v.type || 'list' },
      query:  { view: v.name },
    },
  }))
}

const parsedPublicViews = computed(() => parseViews(getPublicViews()))
const parsedPinnedViews = computed(() => parseViews(getPinnedViews()))

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  await users.promise
})
</script>

<style scoped>
/* ─────────────────────────────────────────────
   Design tokens
───────────────────────────────────────────── */
.sidebar-root {
  --sb-bg:            #FAFAFA;
  --sb-border:        #E8E8E8;
  --sb-active-bg:     #111111;
  --sb-active-fg:     #FFFFFF;
  --sb-hover-bg:      #EFEFEF;
  --sb-fg:            #3A3A3A;
  --sb-muted-fg:      #999999;
  --sb-icon-clr:      #6B6B6B;
  --sb-badge-bg:      #111111;
  --sb-badge-fg:      #FFFFFF;
  --sb-divider:       #E8E8E8;
  --sb-section-fg:    #AAAAAA;
  --sb-sublink-fg:    #707070;
  --sb-radius:        8px;
  --sb-item-h:        34px;
  --sb-icon-sz:       15px;
  --t:                0.16s ease;

  background: var(--sb-bg);
  border-right: 1px solid var(--sb-border);
  font-family: 'DM Sans', ui-sans-serif, system-ui, sans-serif;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Width states (controlled by Tailwind in parent if desired, or CSS here) */
.sidebar-expanded  { width: 220px; min-width: 220px; }
.sidebar-collapsed { width: 48px;  min-width: 48px;  }

/* ─────────────────────────────────────────────
   Scrollbar
───────────────────────────────────────────── */
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }

/* ─────────────────────────────────────────────
   Regions
───────────────────────────────────────────── */
.sidebar-top {
  flex-shrink: 0;
  border-bottom: 1px solid var(--sb-border);
}

.sidebar-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px 5px;
  display: flex;
  flex-direction: column;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 5px;
  border-top: 1px solid var(--sb-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ─────────────────────────────────────────────
   Helpers
───────────────────────────────────────────── */
.nav-divider {
  height: 1px;
  background: var(--sb-divider);
  margin: 5px 3px;
  flex-shrink: 0;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--sb-section-fg);
  padding: 5px 8px 3px;
}

.nav-section-gap {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

/* ─────────────────────────────────────────────
   Nav item
───────────────────────────────────────────── */
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: var(--sb-item-h);
  padding: 0 9px;
  border-radius: var(--sb-radius);
  color: var(--sb-fg);
  font-size: 13px;
  font-weight: 440;
  letter-spacing: -0.01em;
  text-align: left;
  cursor: pointer;
  transition: background var(--t), color var(--t);
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  /* reset button styles */
  background: transparent;
  border: none;
  outline: none;
}

.nav-item:hover {
  background: var(--sb-hover-bg);
  color: #111;
}

.nav-item:hover .nav-icon { color: #111; }

/* Active */
.nav-item--active {
  background: var(--sb-active-bg) !important;
  color: var(--sb-active-fg) !important;
  font-weight: 500;
}
.nav-item--active .nav-icon { color: #FFF !important; }

/* Muted (collapse button) */
.nav-item--muted {
  color: var(--sb-muted-fg);
  font-size: 12.5px;
}
.nav-item--muted:hover { color: #333; }

/* Collapsed state — center the icon */
.nav-item--collapsed {
  justify-content: center;
  padding: 0;
  width: 36px;
  margin-inline: auto;
}

/* Main link inside group takes remaining space */
.nav-item--main { flex: 1; min-width: 0; }

/* ─────────────────────────────────────────────
   Icon
───────────────────────────────────────────── */
.nav-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  color: var(--sb-icon-clr);
  transition: color var(--t);
}

.icon {
  width: var(--sb-icon-sz);
  height: var(--sb-icon-sz);
}

/* ─────────────────────────────────────────────
   Label
───────────────────────────────────────────── */
.nav-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─────────────────────────────────────────────
   Badge
───────────────────────────────────────────── */
.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--sb-badge-bg);
  color: var(--sb-badge-fg);
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
  flex-shrink: 0;
}

.nav-badge-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #EF4444;
  border: 1.5px solid var(--sb-bg);
  pointer-events: none;
}

/* ─────────────────────────────────────────────
   Nav group (item + caret + sublinks)
───────────────────────────────────────────── */
.nav-group {
  display: flex;
  flex-direction: column;
}

.nav-group-header {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* When collapsed, the caret button is gone (v-if) so this just centers the icon button */
.nav-group-header--collapsed {
  justify-content: center;
}

/* ─────────────────────────────────────────────
   Caret
───────────────────────────────────────────── */
.nav-caret {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  color: #C0C0C0;
  cursor: pointer;
  transition: background var(--t), color var(--t), transform 0.2s ease;
  background: transparent;
  border: none;
  outline: none;
}

.nav-caret:hover {
  background: var(--sb-hover-bg);
  color: #444;
}

.nav-caret--open {
  color: #555;
  transform: rotate(90deg);
}

/* ─────────────────────────────────────────────
   Sublinks
───────────────────────────────────────────── */
.sublinks {
  display: flex;
  flex-direction: column;
  margin: 2px 0 3px 17px;
  padding-left: 9px;
  border-left: 1.5px solid var(--sb-divider);
  overflow: hidden;
}

.sublink {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 400;
  color: var(--sb-sublink-fg);
  text-align: left;
  cursor: pointer;
  width: 100%;
  transition: background var(--t), color var(--t);
  white-space: nowrap;
  overflow: hidden;
  background: transparent;
  border: none;
  outline: none;
}

.sublink:hover {
  background: var(--sb-hover-bg);
  color: #111;
}

.sublink:hover .sublink-pip {
  background: #333;
  transform: scale(1.5);
}

.sublink-pip {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #D0D0D0;
  flex-shrink: 0;
  transition: background var(--t), transform 0.15s ease;
}

.sublink-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─────────────────────────────────────────────
   Submenu transition (height + fade)
───────────────────────────────────────────── */
.submenu-enter-active {
  transition: max-height 0.24s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.2s ease;
  max-height: 500px;
}
.submenu-leave-active {
  transition: max-height 0.18s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.14s ease;
}
.submenu-enter-from,
.submenu-leave-to {
  max-height: 0 !important;
  opacity: 0;
}
.submenu-enter-to,
.submenu-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>