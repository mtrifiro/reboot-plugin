// The band's text region, a Client so it hears the pointer: the heading
// and the sentence on what is happening now, and on a right-click a menu
// in the sentence's place. A pick posts to the hooks module, which acts
// with `$`; a right-click again, a pick, or the pointer leaving closes it.
// Beside the sentence, how long it has been showing (or its work has
// run), counted here each second, so it moves between the band's redraws.

import type { ClientModule } from 'claude-code'

/** What the band hands its text region. */
export type BandText = {
  heading: string
  /** A theme color for the heading and its rule; null for the surface's own. */
  headingColor: string | null
  /** How many columns of rule follow the heading (the terminal's), clipped to the room; 0 for none. */
  ruleColumns: number
  line: string | null
  lineColor: string | null
  /** When the sentence's clock started, ms since the epoch; null for one with no timer. */
  since: number | null
  /** The band's clock as it drew, which `since` is measured against. */
  now: number
  menu: {
    /** Whether the dashboard serves, so the menu can open it. */
    canOpenDashboard: boolean
    /** `Copy app address`, `Copy MCP address`; null with nothing to copy. */
    copyLabel: string | null
    isSassy: boolean
  }
}

/** What a pick posts: which item. */
export type MenuPick = { pick: 'dashboard' | 'copy' | 'sassy' }

/**
 * The menu, and the timer's base: the band's clock as last handed in,
 * the local time it came, and a tick that redraws each second.
 */
type State = { isMenuOpen: boolean; propsNow: number; receivedAt: number; tick: number }

/** `45s`, `1m 12s`, as the band writes a time. */
function elapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))

  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`
}

const BandTextRegion: ClientModule<BandText, State> = (p, surface) => {
  const { Box, Button, Text } = surface.elements
  const state = surface.state ?? { isMenuOpen: false, propsNow: p.now, receivedAt: Date.now(), tick: 0 }
  const set = (change: Partial<State>) => surface.setState({ ...(surface.state ?? state), ...change })
  if (surface.state === undefined) {
    surface.setState(state)
    surface.onPointer(e => {
      const isOpen = surface.state?.isMenuOpen ?? false
      if (e.type === 'down' && e.button === 'right') set({ isMenuOpen: !isOpen })
      else if (e.type === 'leave' && isOpen) set({ isMenuOpen: false })
    })
    surface.every(1000, () => set({ tick: (surface.state?.tick ?? 0) + 1 }))
  } else if (state.propsNow !== p.now) {
    // The band drew again: count from its clock, as of now.
    set({ propsNow: p.now, receivedAt: Date.now() })
  }
  const pick = (item: MenuPick['pick']) => {
    set({ isMenuOpen: false })
    surface.post({ pick: item })
  }
  const since = p.since
  const shown = since === null ? null : elapsed(p.now - since + (state.propsNow === p.now ? Date.now() - state.receivedAt : 0))
  const color = p.headingColor ?? undefined

  return (
    <Box flexDirection="column" flexGrow={1}>
      <Box flexDirection="row" height={1} overflow="hidden">
        <Text bold color={color}>
          {p.heading}
        </Text>
        {p.ruleColumns > 0 && (
          <Box flexGrow={1} flexShrink={1} height={1} overflow="hidden" marginLeft={1}>
            <Text color={color}>{'─'.repeat(p.ruleColumns)}</Text>
          </Box>
        )}
      </Box>
      {state.isMenuOpen ? (
        <Box flexDirection="column" height={2}>
          <Box flexDirection="row" gap={1}>
            {p.menu.canOpenDashboard && (
              <Button key="menu-dashboard" label="Open dashboard ↗" onPress={() => pick('dashboard')} />
            )}
            {p.menu.copyLabel !== null && (
              <Button key="menu-copy" label={p.menu.copyLabel} onPress={() => pick('copy')} />
            )}
            <Button key="menu-sassy" label={`${p.menu.isSassy ? '☑' : '☐'} Sassy mode`} onPress={() => pick('sassy')} />
          </Box>
          <Text dimColor>Right-click again to close</Text>
        </Box>
      ) : (
        // Now is a sentence: always two rows, wrapping into the second and
        // clipped past it, so the band keeps its height as it changes; its
        // time at the right of the first row.
        <Box flexDirection="row" height={2} overflow="hidden">
          <Box flexDirection="column" flexGrow={1} flexShrink={1}>
            {p.line !== null && (
              <Text wrap="wrap" color={p.lineColor ?? undefined}>
                {p.line}
              </Text>
            )}
          </Box>
          {p.line !== null && shown !== null && (
            <Box flexShrink={0} marginLeft={1}>
              <Text dimColor>· {shown}</Text>
            </Box>
          )}
        </Box>
      )}
    </Box>
  )
}

export default BandTextRegion
