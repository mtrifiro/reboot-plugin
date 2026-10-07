import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Build } from '../types'
import {
  RUN,
  STEPS,
  backendPort,
  formatStatus,
  isBuildSkill,
  listeningPorts,
  metricsPort,
  stepOf,
} from './progress'
import type { Call, Health } from './progress'

const build = atom({ plugin: 'reboot-progress', key: 'build' } as const, null)
const isHidden = atom({ plugin: 'reboot-progress', key: 'isHidden' } as const, false)
const root = atom({ plugin: 'reboot-progress', key: 'root' } as const, null)

const POLL_MS = 5000

const parent = (path: string) => path.replace(/\/[^/]*$/, '') || '/'

/** The nearest ancestor of `path` holding a `.rbtrc`, up to six levels. */
async function projectOf($: EngineInterface, path: string): Promise<string | null> {
  let dir = parent(path)
  for (let i = 0; i < 6 && dir !== '/'; i++) {
    if (await $.fs.exists(`${dir}/.rbtrc`)) return dir
    dir = parent(dir)
  }

  return null
}

/** The working directory if it is a Reboot project, else its first child that is. */
async function findProject($: EngineInterface): Promise<string | null> {
  const cwd = await $.session.cwd()
  if (await $.fs.exists(`${cwd}/.rbtrc`)) return cwd
  for (const entry of await $.fs.list(cwd)) {
    if (entry.kind === 'dir' && (await $.fs.exists(`${cwd}/${entry.name}/.rbtrc`))) {
      return `${cwd}/${entry.name}`
    }
  }

  return null
}

async function readText($: EngineInterface, path: string): Promise<string> {
  try {
    return await $.fs.read(path)
  } catch {
    return ''
  }
}

async function health($: EngineInterface, dir: string): Promise<Health> {
  const [lsof, ps, rbtrc, webVite] = await Promise.all([
    $.process.run(['lsof', '-nP', '-iTCP', '-sTCP:LISTEN'], { timeoutMs: 5000 }).catch(() => null),
    $.process.run(['ps', '-axo', 'command='], { timeoutMs: 5000 }).catch(() => null),
    readText($, `${dir}/.rbtrc`),
    readText($, `${dir}/web/vite.config.ts`),
  ])
  const ports = listeningPorts(lsof?.stdout ?? '')
  const isMcp = await $.fs.exists(`${dir}/frontend/mcp`)

  // MCP and dual apps run Vite from frontend/ on 4444; a web app from web/.
  let vitePort: number | null = null
  if (await $.fs.exists(`${dir}/frontend/vite.config.ts`)) vitePort = 4444
  else if (webVite) vitePort = Number(webVite.match(/\bport:\s*(\d+)/)?.[1] ?? 5273)

  let tunnel: boolean | null = null
  let url: string | null = null
  if (isMcp) {
    const metrics = metricsPort(ps?.stdout ?? '')
    tunnel = metrics !== null
    if (metrics !== null) {
      try {
        const res = await $.http.fetch(`http://localhost:${metrics}/quicktunnel`)
        const hostname = res.ok ? JSON.parse(res.text).hostname : null
        url = hostname ? `https://${hostname}` : null
      } catch {
        url = null
      }
    }
  }

  return {
    backend: ports.has(backendPort(rbtrc)),
    frontend: vitePort === null ? null : ports.has(vitePort),
    tunnel,
    url,
  }
}

/** The call's fields the classifier reads, or null for other tools. */
function callOf(e: { tool: string } & Record<string, unknown>): Call | null {
  if (e.tool === 'Skill' && typeof e.skill === 'string') return { tool: 'Skill', skill: e.skill }
  if (e.tool === 'Bash' && typeof e.command === 'string') return { tool: 'Bash', command: e.command }
  if ((e.tool === 'Write' || e.tool === 'Edit') && typeof e.file_path === 'string') {
    const text = e.tool === 'Write' ? e.content : e.new_string

    return { tool: e.tool, file_path: e.file_path, text: typeof text === 'string' ? text : '' }
  }

  return null
}

// The module's own; a reload starts them over.
let wasBackendUp = false
let isPolling = false

async function poll($: EngineInterface) {
  if (isPolling) return
  isPolling = true
  try {
    const dir = (await read($, root)) ?? (await findProject($))
    if (!dir) {
      $.ui.status(undefined)
      return
    }
    const h = await health($, dir)
    if (wasBackendUp && !h.backend) $.ui.toast('Reboot backend stopped')
    wasBackendUp = h.backend
    $.ui.status(formatStatus(h))
  } finally {
    isPolling = false
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'reboot-progress',
      description: 'Show, hide or reset the Reboot build progress band',
      argumentHint: '[show|hide|reset]',
    })
    void poll($)
    $.clock.every(POLL_MS, () => void poll($))

    return next(e)
  })

  on('command.run', { command: 'reboot-progress' }, async ($, e) => {
    const arg = e.args.trim()
    if (arg === 'reset') {
      await update($, build, () => null)
      return { text: 'Build progress cleared.' }
    }
    const hide = arg === 'hide' || (arg === '' && !(await read($, isHidden)))
    await update($, isHidden, () => hide)

    return { text: hide ? 'Build progress hidden.' : 'Build progress shown.' }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    const call = callOf(e)
    if (call === null || ran.isError === true || ran.deny !== undefined) return ran

    if (call.tool === 'Write' || call.tool === 'Edit') {
      // Remembering the project is a nicety; never let it cost the band.
      const dir = await projectOf($, call.file_path).catch(() => null)
      if (dir) await update($, root, () => dir)
    }

    const step = stepOf(call)
    if (step === null) return ran

    await update($, build, (b): Build | null => {
      // A build skill opens a new build unless one is under way.
      if (call.tool === 'Skill' && isBuildSkill(call.skill)) {
        return b && !b.isDone ? b : { step: 0, isDone: false }
      }
      // Other evidence only moves a build that is under way, and only forward.
      if (b === null || b.isDone) return b

      return { step: Math.max(b.step, step), isDone: step === RUN }
    })
    if (step === RUN) void poll($)

    return ran
  }).catch(($, e, next) => next(e)) // never block a call on the band's account

  // A finished build shows its last row until the next prompt, then clears.
  on('prompt.submit', async ($, e, next) => {
    const b = await read($, build)
    if (b?.isDone) await update($, build, () => null)

    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const b = await read($, build)
    if (e.props.hasSurvey || b === null || (await read($, isHidden))) return next(e)

    const { Box, Button, Text } = $.ui.resolve(e)
    // Short labels when the row would not fit.
    const isNarrow = e.props.bodyColumns < 100
    const label = (s: string) => (isNarrow ? s.slice(0, 4) : s)

    return (
      <Box flexDirection="row" flexWrap="wrap">
        <Text bold>Build </Text>
        {STEPS.map((s, i) => {
          const isPast = i < b.step || b.isDone
          const isNow = i === b.step && !b.isDone
          const arrow = i < STEPS.length - 1 ? ' → ' : ' '

          return (
            <Text color={isPast ? 'green' : undefined} bold={isNow} dimColor={!isPast && !isNow}>
              {isPast ? '✓ ' : isNow ? '◐ ' : ''}
              {label(s)}
              {arrow}
            </Text>
          )
        })}
        <Button key="hide" label="Hide" onPress={() => update($, isHidden, () => true)} />
      </Box>
    )
  })
}
