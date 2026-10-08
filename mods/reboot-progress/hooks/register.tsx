import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Build, Deploy } from '../types'
import { advanceDeploy, afterOutput, beginDeploy, deployKey, deployLine, isRunning, isShown, outcomeOf, seenIn } from './deploy'
import { REBOOT_LOGO } from './logo'
import { STARTING, WAITING, endTurn, fallback, isWorthSummarizing, parseSummary, startTask, summaryPrompt, textOf } from './activity'
import type { Summary } from './activity'
import {
  RUN,
  advanceTask,
  appLinks,
  asTask,
  backendPort,
  formatStatus,
  beginTask,
  commandKind,
  describeTask,
  listeningPorts,
  finishTurn,
  metricsPort,
  observe,
  skillKind,
  taskAfterPrompt,
  stepOf,
  storeKey,
  UNWATCHED,
} from './progress'
import type { Call, Health, Links, Watch } from './progress'

const build = atom({ plugin: 'reboot-progress', key: 'build' } as const, null)
const isHidden = atom({ plugin: 'reboot-progress', key: 'isHidden' } as const, false)
const root = atom({ plugin: 'reboot-progress', key: 'root' } as const, null)
const deploy = atom({ plugin: 'reboot-progress', key: 'deploy' } as const, null)
const clock = atom({ plugin: 'reboot-progress', key: 'clock' } as const, 0)
const activity = atom({ plugin: 'reboot-progress', key: 'activity' } as const, null)
const links = atom({ plugin: 'reboot-progress', key: 'links' } as const, { dashboard: null, app: null })

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

async function health($: EngineInterface, dir: string): Promise<Health & { links: Links; ps: string }> {
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

  const hasWebApp =
    (await $.fs.exists(`${dir}/web/src`)) || (await $.fs.exists(`${dir}/frontend/web`))

  return {
    backend: ports.has(backendPort(rbtrc)),
    frontend: vitePort === null ? null : ports.has(vitePort),
    tunnel,
    url,
    links: appLinks(ports, { backendPort: backendPort(rbtrc), vitePort, hasWebApp }),
    ps: ps?.stdout ?? '',
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
let appWatch: Watch = UNWATCHED
let dashboardWatch: Watch = UNWATCHED
let isPolling = false
let restoredRoot: string | null = null
let isTurnActive = false
let latestSummary = 0 // the newest summary asked for; older replies are dropped
let lastReply = '' // the model's latest main-thread text, which the next prompt answers

/** A summary while the turn runs moves Now; a late one (the turn's report) only Just completed. */
async function showTask($: EngineInterface, task: Summary) {
  await update($, activity, shown =>
    isTurnActive ? startTask(task, shown) : endTurn(startTask(task, shown)),
  )
}

/**
 * Summarizes `text` with Sonnet in the background, newest wins. A request's
 * summary also says whether it starts new work, which moves the bar to a new
 * task; `decides` is false when a typed slash command already started one.
 */
async function summarize(
  $: EngineInterface,
  text: string,
  kind: 'narration' | 'request',
  decides = kind === 'request',
) {
  const id = ++latestSummary
  let task: Summary | null = null
  try {
    const reply = await $.model.complete({
      model: 'sonnet',
      prompt: summaryPrompt(text, kind, describeTask(await read($, build)), lastReply),
      maxTokens: 80,
      timeoutMs: 15000,
    })
    if (reply.isAnswered) task = parseSummary(reply.text)
  } catch {
    task = null
  }
  // The decision stands even when a newer summary replaces this one's text.
  if (decides && task?.decision) {
    const b = await read($, build)
    const after = taskAfterPrompt(b, task.decision)
    if (after !== b) await saveBuild($, after)
  }
  if (id !== latestSummary) return
  const seen = task ?? { now: fallback(text), done: null, decision: null }
  // A request says what to do, never what is done.
  await showTask($, kind === 'request' ? { ...seen, done: null } : seen)
}

/**
 * Opens `url` in the person's browser. A Link to a local http: address draws
 * as plain text on a remote surface (the desktop app), so the band's links
 * are Buttons that open the address with the system's own command.
 */
async function openUrl($: EngineInterface, url: string) {
  const opened = await $.process.run(['open', url], { timeoutMs: 5000 }).catch(() => null)
  if (opened === null || opened.exitCode !== 0) {
    await $.process.run(['xdg-open', url], { timeoutMs: 5000 }).catch(() => null)
  }
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
  const urls = (await $.store.get(deployKey(dir)).catch(() => null)) as Partial<Deploy> | null
  if ((await read($, deploy)) === null && urls && (urls.apiUrl || urls.siteUrl)) {
    const was = { ...beginDeploy('deployed', 0, null), apiUrl: urls.apiUrl ?? null, siteUrl: urls.siteUrl ?? null }
    await update($, deploy, () => was)
  }
  if ((await read($, build)) !== null) return
  const stored = asTask(await $.store.get(storeKey(dir)))
  // A finished task comes back as it was: Done until new work starts.
  if (stored) await update($, build, () => (stored.isDone ? stored : { ...stored, isRestored: true }))
}

/** Sets the deploy and keeps its URLs for the project across sessions. */
async function saveDeploy($: EngineInterface, d: Deploy | null) {
  const was = await read($, deploy)
  await update($, deploy, () => d)
  if (d === null || (was?.apiUrl === d.apiUrl && was?.siteUrl === d.siteUrl)) return
  // Keeping them for later sessions is a nicety; never let it cost the band.
  try {
    const dir = (await read($, root)) ?? (await findProject($))
    if (dir) await $.store.set(deployKey(dir), { apiUrl: d.apiUrl, siteUrl: d.siteUrl })
  } catch {
    return
  }
}

/** Moves the deploy on by what the process list shows, and the deployed app's answer. */
async function followDeploy($: EngineInterface, ps: string) {
  const d = await read($, deploy)
  const now = await $.clock.now()
  let isServing = false
  if (d?.stage === 'starting' && d.apiUrl) {
    const res = await $.http.fetch(`${d.apiUrl}/__/inspect`).catch(() => null)
    isServing = res?.ok === true
  }
  const after = advanceDeploy(d, seenIn(ps), now, isServing)
  if (after !== d) await saveDeploy($, after)
  if (after?.stage === 'live' && d?.stage === 'starting') $.ui.toast('Reboot Cloud app is live')
  // Ticks while the band shows the deploy, and once more to take it away.
  if (isShown(after, now) || isShown(d, await read($, clock))) await update($, clock, () => now)
}

/** Toasts when the app (its backend) or the dashboard starts or stops. */
function announce($: EngineInterface, server: 'app' | 'dashboard', isUp: boolean) {
  const { watch, change } = observe(server === 'app' ? appWatch : dashboardWatch, isUp)
  if (server === 'app') appWatch = watch
  else dashboardWatch = watch
  if (change) $.ui.toast(`Reboot ${server} ${change}`)
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
    // The band's links first: a failed status line must not cost them.
    const was = await read($, links)
    if (was.dashboard !== h.links.dashboard || was.app !== h.links.app) await update($, links, () => h.links)
    await followDeploy($, h.ps).catch(() => undefined)
    announce($, 'app', h.backend)
    announce($, 'dashboard', h.links.dashboard !== null)
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
    // A deploy shows the moment it starts, and its output, once a tool's
    // result carries it (a failed one's too), says how it ended and where
    // it lives.
    if (e.tool === 'Bash' && /\brbt\s+cloud\s+up\b/.test(String(e.command)) && !isRunning(await read($, deploy))) {
      await saveDeploy($, beginDeploy('checking', await $.clock.now(), await read($, deploy)))
    }
    const ran = await next(e)
    // Command output only: a Bash call's, or a background one's read back.
    const isOutput =
      e.tool === 'Bash' || e.tool === 'GetTask' || (e.tool === 'Read' && /\.output$/.test(String(e.file_path)))
    const text = isOutput ? (ran.text ?? '') : ''
    if (/Your API is available at|Could not deploy revision|🛑|\.pages\.dev/.test(text)) {
      const now = await $.clock.now()
      const { deploy: after, toast } = afterOutput(await read($, deploy), outcomeOf(text), now)
      await saveDeploy($, after)
      await update($, clock, () => now)
      if (toast) $.ui.toast(toast)
    }

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
    const kind = call.tool === 'Skill' ? skillKind(call.skill) : null
    const after = kind !== null ? beginTask(b, kind) : advanceTask(b, step)
    if (JSON.stringify(after) !== JSON.stringify(b)) await saveBuild($, after)
    if (step === RUN) void poll($)

    return ran
  }).catch(($, e, next) => next(e)) // never block a call on the band's account

  // A finished task keeps its full Done bar until new work starts: a typed
  // slash command now, or the prompt's summary saying it is new work.
  on('prompt.submit', async ($, e, next) => {
    isTurnActive = true
    // Never "Idle" while a turn runs: until the summary names the
    // work, Now says the request is being worked on.
    await update($, activity, shown => ({ justCompleted: shown?.justCompleted ?? null, now: STARTING }))
    const b = await read($, build)
    // A typed /reboot:app (or build, mcp-ui, web-app, feature) starts its
    // task now, before the skill's planning, not when the model calls it.
    const kind = commandKind(e.text)
    if (kind !== null) {
      const after = beginTask(b?.isDone ? null : b, kind)
      if (JSON.stringify(after) !== JSON.stringify(b)) await saveBuild($, after)
    }
    if (e.text.trim()) void summarize($, e.text, 'request', kind === null)

    return next(e)
  }).catch(($, e, next) => next(e))

  // The model's own narration on the main thread, not a subagent's.
  on('session.append', { door: 'response' }, async ($, e, next) => {
    const appended = await next(e)
    if (e.agentId === undefined && e.message.type === 'assistant') {
      const text = textOf(e.message.content)
      if (text) lastReply = text
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
    const to = await read($, links)
    const d = await read($, deploy)
    const now = await read($, clock)
    const cloud = d?.apiUrl ?? null
    const site = d?.siteUrl ?? null
    const hasLinks = to.dashboard !== null || to.app !== null || cloud !== null || site !== null
    // A running deploy takes Now's place, with the time it has taken.
    const line = isShown(d, now) ? deployLine(d!, Math.max(now, d!.stageAt)) : (act?.now ?? null)
    if (e.props.hasSurvey || (b === null && line === null && !hasLinks) || (await read($, isHidden))) {
      return next(e)
    }

    const elements = $.ui.resolve(e)
    const { Box, Button, Text } = elements
    // Svg is on every surface but the terminal's.
    const Svg = 'Svg' in elements ? elements.Svg : null
    // The terminal has no logo, so color carries it there, in the theme's
    // own colors to read on a light or dark background; other surfaces
    // keep their look.
    const isTerminal = e.surface === 'terminal'
    const deployColor = !isShown(d, now) ? undefined : d!.stage === 'failed' ? 'error' : 'warning'
    // On top, a bold Status heading with Reboot at the right margin; below
    // it what is happening now on the left, the links on the right.

    return (
      <Box flexDirection="column">
        <Box flexDirection="row" justifyContent="space-between">
          <Box flexGrow={1}>
            <Text bold color={isTerminal ? 'success' : undefined}>
              Status
            </Text>
          </Box>
          <Box flexShrink={0} flexDirection="row" gap={1} alignItems="center">
            {/* A link's address, shown while the pointer is on its button below. */}
            {to.dashboard !== null && (
              <Box display="none" hover={{ scope: 'link-dashboard', display: 'flex' }}>
                <Text dimColor>Opens the dashboard: {to.dashboard}</Text>
              </Box>
            )}
            {to.app !== null && (
              <Box display="none" hover={{ scope: 'link-app', display: 'flex' }}>
                <Text dimColor>Opens the app: {to.app}</Text>
              </Box>
            )}
            {cloud !== null && (
              <Box display="none" hover={{ scope: 'link-cloud', display: 'flex' }}>
                <Text dimColor>Opens the app on Reboot Cloud: {cloud}</Text>
              </Box>
            )}
            {site !== null && (
              <Box display="none" hover={{ scope: 'link-site', display: 'flex' }}>
                <Text dimColor>Opens the published site: {site}</Text>
              </Box>
            )}
            {/* The favicon where the surface draws Svg. */}
            {Svg && <Svg source={REBOOT_LOGO} alt="Reboot logo" width={14} height={14} />}
            <Text bold color={isTerminal ? 'success' : undefined}>
              Reboot
            </Text>
          </Box>
        </Box>
        <Box flexDirection="row" justifyContent="space-between">
          {/* Now is a sentence: it takes the free width and always two rows,
              wrapping into the second and clipped past it, so the band keeps
              its height as the sentence changes; the buttons keep their width. */}
          <Box flexDirection="column" flexGrow={1} flexShrink={1} height={2} overflow="hidden">
            {line !== null && (
              <Text wrap="wrap" color={isTerminal ? deployColor : undefined}>
                {line}
              </Text>
            )}
          </Box>
          <Box flexDirection="row" gap={1} flexShrink={0}>
            {to.dashboard !== null && (
              <Box hover={{ scope: 'link-dashboard' }}>
                <Button key="dashboard" label="Dashboard ↗" onPress={() => openUrl($, to.dashboard!)} />
              </Box>
            )}
            {to.app !== null && (
              <Box hover={{ scope: 'link-app' }}>
                <Button key="app" label="App ↗" onPress={() => openUrl($, to.app!)} />
              </Box>
            )}
            {cloud !== null && (
              <Box hover={{ scope: 'link-cloud' }}>
                <Button key="cloud" label="Cloud ↗" onPress={() => openUrl($, cloud)} />
              </Box>
            )}
            {site !== null && (
              <Box hover={{ scope: 'link-site' }}>
                <Button key="site" label="Site ↗" onPress={() => openUrl($, site)} />
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    )
  })
}
