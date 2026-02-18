import { usersStore } from '@/stores/users'
import { dayjs, createListResource } from 'frappe-ui'
import { sameArrayContents } from '@/utils'
import { computed, ref } from 'vue'
import { allTimeSlots } from '@/components/Calendar/utils'

export const showEventModal = ref(false)
export const activeEvent = ref(null)

/* =========================
   MAIN COMPOSABLE
========================= */
export function useEvent(doctype, docname) {
    const { getUser } = usersStore()

    const eventsResource = createListResource({
        doctype: 'Event',
        cache: ['calendar', docname],
        fields: [
            'name',
            'status',
            'subject',
            'description',
            'starts_on',
            'ends_on',
            'all_day',
            'event_type',
            'color',
            'owner',
            'reference_doctype',
            'reference_docname',
            'creation',
        ],
        filters: {
            reference_doctype: doctype,
            reference_docname: docname,
        },
        auto: true,
        orderBy: 'creation desc',
    })

    const eventParticipantsResource = createListResource({
        doctype: 'Event Participants',
        fields: ['*'],
        parent: 'Event',
    })

    const events = computed(() => {
        if (!eventsResource.data) return []

        const eventNames = eventsResource.data.map(e => e.name)

        if (
            !eventParticipantsResource.data?.length ||
            eventsParticipantIsUpdated(eventNames)
        ) {
            eventParticipantsResource.update({
                filters: {
                    parenttype: 'Event',
                    parentfield: 'event_participants',
                    parent: ['in', eventNames],
                },
            })
            !eventParticipantsResource.list.loading &&
                eventParticipantsResource.reload()
            return eventsResource.data
        }

        eventsResource.data.forEach(event => {
            if (typeof event.owner !== 'object') {
                const u = getUser(event.owner)
                event.owner = {
                    label: u?.full_name || event.owner,
                    image: u?.user_image || '',
                    name: event.owner,
                }
            }

            event.event_participants =
                eventParticipantsResource.data.filter(
                    p => p.parent === event.name
                )

            event.participants = [
                event.owner,
                ...event.event_participants.map(p => {
                    const u = getUser(p.email)
                    return {
                        label: u?.full_name || p.email,
                        image: u?.user_image || '',
                        name: p.email,
                    }
                }),
            ]
        })

        return eventsResource.data
    })

    function eventsParticipantIsUpdated(eventNames) {
        const parentFilter = eventParticipantsResource.filters?.parent?.[1]

        if (eventNames.length && !sameArrayContents(parentFilter, eventNames)) {
            return true
        }

        const d = eventsResource.setValue?.data
        if (!d) return false

        const newParticipants = d.event_participants?.map(p => p.name) || []
        const oldParticipants =
            eventParticipantsResource.data
                ?.filter(p => p.parent === d.name)
                .map(p => p.name) || []

        return !sameArrayContents(newParticipants, oldParticipants)
    }

    return {
        eventsResource,
        eventParticipantsResource,
        events,
    }
}

/* =========================
   HELPERS
========================= */
export function normalizeParticipants(list = []) {
    const seen = new Set()
    const out = []

    for (const a of list) {
        if (!a?.email || seen.has(a.email)) continue
        seen.add(a.email)
        out.push({
            email: a.email,
            reference_doctype: a.reference_doctype || 'Contact',
            reference_docname: a.reference_docname || '',
        })
    }
    return out
}

export function formatDuration(mins) {
    if (mins < 60) return __('{0} mins', [mins])
    let hours = mins / 60
    if (hours % 1 !== 0 && hours % 1 !== 0.5) {
        hours = hours.toFixed(2)
    }
    if (Number.isInteger(+hours)) {
        return +hours === 1 ? __('1 hr') : __('{0} hrs', [hours])
    }
    return `${hours} hrs`
}

export function buildEndTimeOptions(fromTime) {
    const timeSlots = allTimeSlots()
    if (!fromTime) return timeSlots

    const startIndex = timeSlots.findIndex(o => o.value > fromTime)
    if (startIndex === -1) return []

    const [fh, fm] = fromTime.split(':').map(Number)
    const fromTotal = fh * 60 + fm

    return timeSlots.slice(startIndex).map(o => {
        const [th, tm] = o.value.split(':').map(Number)
        const duration = th * 60 + tm - fromTotal
        return {
            ...o,
            label: `${o.label} (${formatDuration(duration)})`,
        }
    })
}

export function computeAutoToTime(fromTime) {
    if (!fromTime) return ''
    const [h, m] = fromTime.split(':').map(Number)
    let nh = h + 1
    let nm = m
    if (nh >= 24) {
        nh = 23
        nm = 59
    }
    return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`
}

export function validateTimeRange({ fromDate, fromTime, toTime, isFullDay }) {
    if (isFullDay) return { valid: true, error: null }

    if (!fromTime || !toTime) {
        return { valid: false, error: __('Start and end time are required') }
    }

    const start = dayjs(`${fromDate} ${fromTime}`)
    const end = dayjs(`${fromDate} ${toTime}`)

    if (!start.isValid() || !end.isValid()) {
        return { valid: false, error: __('Invalid start or end time') }
    }

    if (end.diff(start, 'minute') <= 0) {
        return { valid: false, error: __('End time should be after start time') }
    }

    return { valid: true, error: null }
}

/* =========================
   PARSER
========================= */
export function parseEventDoc(doc) {
    if (!doc) return {}
    const { getUser } = usersStore()
    const u = getUser(doc.owner)

    return {
        id: doc.name,
        title: doc.subject,
        description: doc.description,
        status: doc.status,
        fromDate: dayjs(doc.starts_on).format('YYYY-MM-DD'),
        toDate: dayjs(doc.ends_on).format('YYYY-MM-DD'),
        fromTime: dayjs(doc.starts_on).format('HH:mm'),
        toTime: dayjs(doc.ends_on).format('HH:mm'),
        isFullDay: doc.all_day,
        eventType: doc.event_type,
        color: doc.color,
        referenceDoctype: doc.reference_doctype,
        referenceDocname: doc.reference_docname,
        event_participants: doc.event_participants || [],
        owner: doc.owner
            ? {
                label: u?.full_name || doc.owner,
                image: u?.user_image || '',
                value: doc.owner,
            }
            : null,
    }
}
