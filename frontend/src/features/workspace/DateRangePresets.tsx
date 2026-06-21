import { useWorkspaceStore } from '@/store/workspaceStore'
import type { DatePreset } from '@/lib/types'

// ── helpers ──────────────────────────────────────────────────────────────────

function toISODate(d: Date): string {
  return d.toISOString().split('T')[0]
}

function computePreset(
  preset: Exclude<DatePreset, 'personalizado'>,
): { since: string; until: string } {
  const today = new Date()
  const until = toISODate(today)
  switch (preset) {
    case 'hoje':
      return { since: until, until }
    case 'ultimos7': {
      const d = new Date(today)
      d.setDate(d.getDate() - 6)
      return { since: toISODate(d), until }
    }
    case 'ultimos15': {
      const d = new Date(today)
      d.setDate(d.getDate() - 14)
      return { since: toISODate(d), until }
    }
    case 'ultimos30': {
      const d = new Date(today)
      d.setDate(d.getDate() - 29)
      return { since: toISODate(d), until }
    }
    case 'estemes': {
      const d = new Date(today.getFullYear(), today.getMonth(), 1)
      return { since: toISODate(d), until }
    }
  }
}

/** Format YYYY-MM-DD → DD/MM/YYYY for display */
function fmtDate(iso: string): string {
  const [y, m, day] = iso.split('-')
  return `${day}/${m}/${y}`
}

const NON_CUSTOM_PRESETS: Exclude<DatePreset, 'personalizado'>[] = [
  'hoje',
  'ultimos7',
  'ultimos15',
  'ultimos30',
  'estemes',
]

const PRESET_LABELS: Record<DatePreset, string> = {
  hoje: 'Hoje',
  ultimos7: 'Últ. 7 dias',
  ultimos15: 'Últ. 15 dias',
  ultimos30: 'Últ. 30 dias',
  estemes: 'Este mês',
  personalizado: 'Personalizado',
}

/** Detect which preset matches the current since/until pair (if any) */
function detectActivePreset(since: string | undefined, until: string | undefined): DatePreset {
  if (!since && !until) return 'personalizado'
  for (const p of NON_CUSTOM_PRESETS) {
    const computed = computePreset(p)
    if (computed.since === since && computed.until === until) return p
  }
  return 'personalizado'
}

// ── component ─────────────────────────────────────────────────────────────────

export function DateRangePresets() {
  const draftFilters = useWorkspaceStore((s) => s.draftFilters)
  const setDraftFilter = useWorkspaceStore((s) => s.setDraftFilter)

  const activePreset = detectActivePreset(draftFilters.since, draftFilters.until)

  function handlePreset(preset: DatePreset) {
    if (preset === 'personalizado') {
      // Just switch UI mode; keep existing since/until if any
      // Force "personalizado" by clearing to empty so detectActivePreset returns 'personalizado'
      // Only do this if we're currently on a named preset (to avoid losing custom input)
      if (activePreset !== 'personalizado') {
        setDraftFilter({ since: undefined, until: undefined })
      }
    } else {
      const range = computePreset(preset)
      setDraftFilter(range)
    }
  }

  const isCustom = activePreset === 'personalizado'

  return (
    <div className="flex flex-col gap-2">
      {/* Preset button row */}
      <div className="flex flex-wrap gap-1">
        {(Object.keys(PRESET_LABELS) as DatePreset[]).map((preset) => {
          const isActive = activePreset === preset
          return (
            <button
              key={preset}
              type="button"
              onClick={() => handlePreset(preset)}
              className={[
                'px-2 py-1 text-xs rounded border transition-colors',
                isActive
                  ? 'ring-2 ring-blue-500 bg-blue-50 border-blue-400 text-blue-700 font-semibold'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
              ].join(' ')}
            >
              {PRESET_LABELS[preset]}
            </button>
          )
        })}
      </div>

      {/* Resolved date display for named presets */}
      {!isCustom && draftFilters.since && draftFilters.until && (
        <p className="text-xs text-gray-500">
          De: {fmtDate(draftFilters.since)}&nbsp;&nbsp;Até: {fmtDate(draftFilters.until)}
        </p>
      )}

      {/* Custom date inputs */}
      {isCustom && (
        <div className="flex gap-2 items-center">
          <div className="flex flex-col gap-0.5">
            <label className="text-xs text-gray-500">De</label>
            <input
              type="date"
              className="text-xs border border-gray-300 rounded px-1 py-0.5"
              value={draftFilters.since ?? ''}
              onChange={(e) => setDraftFilter({ since: e.target.value || undefined })}
            />
          </div>
          <div className="flex flex-col gap-0.5">
            <label className="text-xs text-gray-500">Até</label>
            <input
              type="date"
              className="text-xs border border-gray-300 rounded px-1 py-0.5"
              value={draftFilters.until ?? ''}
              onChange={(e) => setDraftFilter({ until: e.target.value || undefined })}
            />
          </div>
        </div>
      )}
    </div>
  )
}
