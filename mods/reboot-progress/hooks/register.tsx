import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Build } from '../types'
import { WAITING, endTurn, fallback, isWorthSummarizing, parseSummary, startTask, summaryPrompt, textOf } from './activity'
import type { Task } from './activity'
import {
  RUN,
  asBuild,
  backendPort,
  barRuns,
  barWidth,
  formatStatus,
  isBuildSkill,
  listeningPorts,
  finishTurn,
  metricsPort,
  nextBuild,
  progressBar,
  stepOf,
  storeKey,
} from './progress'
import type { Call, Health } from './progress'

const build = atom({ plugin: 'reboot-progress', key: 'build' } as const, null)
const isHidden = atom({ plugin: 'reboot-progress', key: 'isHidden' } as const, false)
const root = atom({ plugin: 'reboot-progress', key: 'root' } as const, null)
const activity = atom({ plugin: 'reboot-progress', key: 'activity' } as const, null)

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
let restoredRoot: string | null = null
let isTurnActive = false
let latestSummary = 0 // the newest summary asked for; older replies are dropped

/** A summary while the turn runs moves Now; a late one (the turn's report) only Just completed. */
async function showTask($: EngineInterface, task: Task) {
  await update($, activity, shown =>
    isTurnActive ? startTask(task, shown) : endTurn(startTask(task, shown)),
  )
}

/** Summarizes `text` with Sonnet in the background, newest wins. */
async function summarize($: EngineInterface, text: string, kind: 'narration' | 'request') {
  const id = ++latestSummary
  let task: Task | null = null
  try {
    const reply = await $.model.complete({
      model: 'sonnet',
      prompt: summaryPrompt(text, kind),
      maxTokens: 60,
      timeoutMs: 15000,
    })
    if (reply.isAnswered) task = parseSummary(reply.text)
  } catch {
    task = null
  }
  if (id !== latestSummary) return
  const seen = task ?? { now: fallback(text), done: null }
  // A request says what to do, never what is done.
  await showTask($, kind === 'request' ? { ...seen, done: null } : seen)
}

/** Sets the session's build and keeps it for the project across sessions. */
async function saveBuild($: EngineInterface, b: Build | null) {
  await update($, build, () => b)
  // Keeping it for later sessions is a nicety; never let it cost the band.
  try {
    const dir = (await read($, root)) ?? (await findProject($))
    if (!dir) return
    if (b === null) await $.store.delete(storeKey(dir))
    else await $.store.set(storeKey(dir), b)
  } catch {
    return
  }
}

/** Once per project: a session that finds one picks up its stored build. */
async function restoreBuild($: EngineInterface, dir: string) {
  if (restoredRoot === dir) return
  restoredRoot = dir
  if ((await read($, build)) !== null) return
  const stored = asBuild(await $.store.get(storeKey(dir)))
  if (stored && !stored.isDone) await update($, build, () => ({ ...stored, isRestored: true }))
}

async function poll($: EngineInterface) {
  if (isPolling) return
  isPolling = true
  try {
    const dir = (await read($, root)) ?? (await findProject($))
    if (!dir) {
      $.ui.status(undefined)
      return
    }
    // Each part on its own: a failed restore must not cost the status line.
    await restoreBuild($, dir).catch(() => undefined)
    const h = await health($, dir).catch(() => null)
    if (h === null) return
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
      description: 'Show, hide or reset the band above the prompt (activity and build progress)',
      argumentHint: '[show|hide|reset]',
    })
    await update($, activity, () => ({ justCompleted: null, now: WAITING }))
    void poll($)
    $.clock.every(POLL_MS, () => void poll($))

    return next(e)
  })

  on('command.run', { command: 'reboot-progress' }, async ($, e) => {
    const arg = e.args.trim()
    if (arg === 'reset') {
      await saveBuild($, null)
      return { text: 'Build progress cleared.' }
    }
    const hide = arg === 'hide' || (arg === '' && !(await read($, isHidden)))
    await update($, isHidden, () => hide)

    return { text: hide ? 'Band hidden.' : 'Band shown.' }
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

    const b = await read($, build)
    const after = nextBuild(b, step, call.tool === 'Skill' && isBuildSkill(call.skill))
    if (JSON.stringify(after) !== JSON.stringify(b)) await saveBuild($, after)
    if (step === RUN) void poll($)

    return ran
  }).catch(($, e, next) => next(e)) // never block a call on the band's account

  // A finished build shows its last row until the next prompt, then clears.
  on('prompt.submit', async ($, e, next) => {
    isTurnActive = true
    if (e.text.trim()) void summarize($, e.text, 'request')
    const b = await read($, build)
    if (b?.isDone) await saveBuild($, null)

    return next(e)
  }).catch(($, e, next) => next(e))

  // The model's own narration on the main thread, not a subagent's.
  on('session.append', { door: 'response' }, async ($, e, next) => {
    const appended = await next(e)
    if (e.agentId === undefined && e.message.type === 'assistant') {
      const text = textOf(e.message.content)
      if (isWorthSummarizing(text)) void summarize($, text, 'narration')
    }

    return appended
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    isTurnActive = false
    const b = await read($, build)
    const finished = finishTurn(b)
    if (finished !== b) await saveBuild($, finished)
    await update($, activity, shown => endTurn(shown))

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const b = await read($, build)
    const act = await read($, activity)
    if (e.props.hasSurvey || (b === null && act === null) || (await read($, isHidden))) return next(e)

    const { Box, Text } = $.ui.resolve(e)
    const bar = b && progressBar(b.step, b.isDone, barWidth(e.props.bodyColumns))

    // The Reboot bar on top; below it two columns, each a label over its status.
    const column = Math.max(16, Math.floor(e.props.bodyColumns / 2))

    return (
      <Box flexDirection="column">
        {bar && (
          <Box flexDirection="row" flexWrap="wrap">
            <Text bold>Reboot  </Text>
            {barRuns(bar.filled, bar.filled + bar.empty).map(run => (
              <Text color={run.color}>{'█'.repeat(run.cells)}</Text>
            ))}
            <Text dimColor>{'░'.repeat(bar.empty)}</Text>
          </Box>
        )}
        {act !== null && (
          <Box flexDirection="row">
            <Box flexDirection="column" width={column}>
              <Text bold>Just completed</Text>
              {/* Until this session finishes a task. */}
              {act.justCompleted === null ? (
                <Text dimColor italic>nothing this session</Text>
              ) : (
                <Text dimColor wrap="truncate-end">{act.justCompleted}</Text>
              )}
            </Box>
            <Box flexDirection="column" width={column}>
              <Text bold>Now</Text>
              <Text wrap="truncate-end">{act.now}</Text>
            </Box>
          </Box>
        )}
      </Box>
    )
  })
}
