// Pure logic: where a deploy is, read from the process list while it runs
// and from its output once a tool's result carries it. `rbt cloud up`
// (reboot 1.6.0, cli/commands/cloud/up.py) checks permissions, runs
// `docker build` and `docker push`, then waits on the new revision; its
// app answers 503 for about 30 seconds after it exits. `wrangler pages
// deploy` publishes the frontend.

import type { Deploy, DeployStage } from '../types'

/** Stages a deploy is still in: the band shows them, with the time so far. */
const RUNNING = new Set<DeployStage>(['checking', 'build', 'push', 'rollout', 'starting', 'publish'])

/** The stages `rbt cloud up` itself is in while it runs. */
const UP = new Set<DeployStage>(['checking', 'build', 'push', 'rollout'])

export const isRunning = (d: Deploy | null): boolean => d !== null && RUNNING.has(d.stage)

/** Whether the deploy is in a stage `rbt cloud up` itself runs. */
export const isUp = (d: Deploy | null): boolean => d !== null && UP.has(d.stage)

/** How long a deploy script may run its own steps before `rbt cloud up` shows, before it counts as over. */
export const SCRIPT_MS = 20 * 60 * 1000

/** How long a failed deploy stays in the band after it fails. */
export const FAILED_MS = 2 * 60 * 1000

/** Whether the band shows the deploy: while it runs, and for a while after it fails. */
export const isShown = (d: Deploy | null, now: number): boolean =>
  isRunning(d) || (d?.stage === 'failed' && now - d.stageAt < FAILED_MS)

/** How long a revision may answer 503 before the band stops waiting on it. */
export const STARTING_MS = 5 * 60 * 1000

/** What the process list shows of a deploy. */
export type Seen = { isUp: boolean; isBuild: boolean; isPush: boolean; isPublish: boolean }

/**
 * A deploy's processes in `ps -axo pid=,command=` output. Only a process
 * that runs the deploy counts: `rbt cloud up` or `wrangler pages deploy`
 * as its own program (or a script an interpreter runs), never a `grep`,
 * a test or a shell whose arguments merely contain those words.
 */
export function seenIn(ps: string): Seen {
  const lines = ps.split('\n')
  const has = (re: RegExp) => lines.some(l => re.test(l))
  const runs = (program: 'up' | 'publish') => lines.some(l => psProgram(l) === program)

  return {
    isUp: runs('up'),
    isBuild: has(/\bdocker\b.*\s(build|buildx\s+build)\s/),
    isPush: has(/\bdocker\b.*\spush\s/),
    isPublish: runs('publish'),
  }
}

/**
 * The deploy one process-list line runs, if any: its pid dropped, and an
 * interpreter running a script (`python3 …/bin/rbt cloud up`, `node
 * …/wrangler pages deploy`) read as that script.
 */
export function psProgram(line: string): 'up' | 'publish' | 'script' | null {
  const words = line.trim().replace(/^\d+\s+/, '').split(/\s+/)
  if (/(^|\/)(python[\d.]*|node|bun|deno)$/.test(words[0] ?? '')) {
    words.shift()
    while ((words[0] ?? '').startsWith('-')) words.shift()
  }
  return deployProgram(words.join(' '))
}

/** A new deploy at `stage`, keeping the URLs of the one before. */
export const beginDeploy = (stage: DeployStage, now: number, was: Deploy | null, source?: Deploy['source']): Deploy => ({
  stage,
  ...(source ? { source } : {}),
  startedAt: now,
  stageAt: now,
  revision: null,
  apiUrl: was?.apiUrl ?? null,
  siteUrl: was?.siteUrl ?? null,
  failure: null,
})

/**
 * The deploy after a poll. A deploy starts when its processes appear;
 * `rbt cloud up` moves through its stages by the Docker processes under it
 * (with none, it is checking before the build and rolling out after); once
 * it exits, the revision is starting while its URL is known, else deployed.
 * Publishing ends when wrangler exits. `isServing` is whether the deployed
 * app answers, for a deploy that is starting.
 */
export function advanceDeploy(d: Deploy | null, seen: Seen, now: number, isServing = false): Deploy | null {
  const active = isRunning(d)
  if (!active && seen.isUp) return beginDeploy(seen.isPush ? 'push' : seen.isBuild ? 'build' : 'checking', now, d, 'up')
  if (!active && seen.isPublish) return beginDeploy('publish', now, d, 'publish')
  if (d === null || !active) return d

  if (UP.has(d.stage)) {
    if (seen.isUp) {
      const stage: DeployStage = seen.isPush
        ? 'push'
        : seen.isBuild
          ? 'build'
          : d.stage === 'checking'
            ? 'checking'
            : 'rollout'
      return stage === d.stage ? d : { ...d, stage, stageAt: now }
    }
    // A deploy script runs its own checks and a backup before `rbt cloud
    // up` shows in the process list: not over until it has, or it has run
    // too long to still be checking.
    if (d.source === 'script' && d.stage === 'checking' && now - d.startedAt < SCRIPT_MS) return d
    // Exited without its output read yet: starting if the URL is known.
    return { ...d, stage: d.apiUrl ? 'starting' : 'deployed', stageAt: now }
  }
  if (d.stage === 'starting') {
    if (isServing) return { ...d, stage: 'live', stageAt: now }
    if (now - d.stageAt > STARTING_MS) return { ...d, stage: 'deployed', stageAt: now }
    return d
  }
  if (d.stage === 'publish' && !seen.isPublish) return { ...d, stage: 'published', stageAt: now }

  return d
}

/**
 * Whether a command is a deploy, whose output may say how one ended and
 * where it lives: `rbt cloud up`, `wrangler pages deploy`, or a
 * project's `scripts/deploy.sh`. Any other command's output (a doc
 * printed, a ledger read) only mentions a deploy, and is not one.
 */
export function isDeployCommand(command: string): boolean {
  return deployProgram(command) !== null
}

/**
 * Which deploy a command runs, if any: `up` (`rbt cloud up`), `publish`
 * (`wrangler pages deploy`) or `script` (a project's `scripts/deploy.sh`,
 * not its `--dry-run`). Each piece of a compound command counts as the
 * program it runs, past a `(`, `VAR=value`s, wrappers (`timeout 900`,
 * `nohup`, `env`, `time`), runners (`uv run --directory app`, `uvx`,
 * `npx -y`, `bunx`, `pnpm dlx`, `bash -lc`) and a path to the program
 * (`.venv/bin/rbt`); a heredoc's body is text. So `cat scripts/deploy.sh`,
 * `grep "rbt cloud up" doc.md`, or a script or test that merely contains
 * those words, is not a deploy.
 */
export function deployProgram(command: string): 'up' | 'publish' | 'script' | null {
  const text = command.replace(/<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2(?=\s|$)/g, '')
  for (const piece of text.split(/&&|\|\||[;|\n]/)) {
    const words = programWords(piece)
    const program = words[0] ?? ''
    if (program === 'rbt' && words[1] === 'cloud' && words[2] === 'up') return 'up'
    if (/^wrangler(@\S+)?$/.test(program) && words[1] === 'pages' && words[2] === 'deploy') return 'publish'
    if (/^(\S*\/)?scripts\/deploy\.sh$/.test(program)) return words.includes('--dry-run') ? null : 'script'
  }
  return null
}

/** The programs that only run the one after them, with the flags each takes before it. */
const PROGRAM = /^(\S*\/)?(rbt|wrangler(@\S+)?|scripts\/deploy\.sh)$/

/** A piece of a command as words, from the program it runs on: wrappers, runners and quotes stripped. */
function programWords(piece: string): string[] {
  const words = piece.trim().replace(/^\(\s*/, '').split(/\s+/).filter(w => w !== '')
  for (;;) {
    const w = words[0] ?? ''
    if (PROGRAM.test(w.replace(/^['"]|['"]$/g, ''))) break
    if (/^\w+=/.test(w) || /^(nohup|env|time|exec)$/.test(w)) words.shift()
    else if (w === 'timeout') {
      words.shift()
      while (words.length > 0 && /^-/.test(words[0]!)) words.shift()
      if (/^\d+[smhd]?$/.test(words[0] ?? '')) words.shift()
    } else if (w === 'uv' && words[1] === 'run') {
      words.splice(0, 2)
      while (words.length > 0 && /^-/.test(words[0]!)) {
        const flag = words.shift()!
        // A flag with its value apart (`--directory app`), unless the next word is the program.
        if (!flag.includes('=') && words.length > 0 && !PROGRAM.test(words[0]!) && !/^-/.test(words[0]!)) words.shift()
      }
    } else if (w === 'uvx') {
      words.shift()
      while (words.length > 0 && /^-/.test(words[0]!)) words.shift()
    } else if (w === 'npx') {
      words.shift()
      while (words.length > 0 && /^(-y|--yes)$/.test(words[0]!)) words.shift()
    } else if (w === 'bunx' || (w === 'pnpm' && words[1] === 'dlx')) {
      words.splice(0, w === 'bunx' ? 1 : 2)
    } else if (/^(bash|sh|zsh)$/.test(w)) {
      words.shift()
      while (words.length > 0 && /^-/.test(words[0]!)) words.shift()
      // `bash -lc 'scripts/deploy.sh'`: the quoted script is the command.
      const quoted = words.join(' ').match(/^(['"])(.*)\1$/)
      if (quoted) return programWords(quoted[2]!)
    } else break
    if (words.length === 0) return []
  }
  if (words.length > 0) words[0] = words[0]!.replace(/^['"]|['"]$/g, '').replace(/^\S*\/(?=(rbt|wrangler|scripts\/deploy\.sh)\b)/, '')
  return words
}

/** What a tool's output says of a deploy. */
export type Outcome = {
  apiUrl: string | null
  revision: number | null
  failure: string | null
  siteUrl: string | null
}

/** A deploy's outcome in a tool's output text: `rbt cloud up`'s, `wrangler`'s. */
export function outcomeOf(text: string): Outcome {
  const api = text.match(/Your API is available at:\s*(https:\/\/\S+)/)
  const revision = text.match(/revision (\d+) is\s+available/)
  const failed =
    text.match(/Could not deploy revision \d+:\s*\n\s*(.+)/) ?? text.match(/🛑 (?:failed:\s*\n?\s*)?(.+)/)
  // Wrangler names the `*.pages.dev` site; a project's deploy script
  // names the custom domain it serves (`https://app.example.com serves …`).
  const site = text.match(/https:\/\/[\w.-]+\.pages\.dev\b/) ?? text.match(/(https:\/\/[\w.-]+(?::\d+)?)\/?\s+serves\b/)

  return {
    apiUrl: api ? api[1]!.replace(/\/+$/, '') : null,
    revision: revision ? Number(revision[1]) : null,
    failure: failed ? failed[1]!.trim() : null,
    siteUrl: site ? `${(site[1] ?? site[0]).replace(/\/+$/, '')}/` : null,
  }
}

/**
 * The deploy after a tool's output, and the toast to show. A success or a
 * failure counts only for a deploy under way; the URLs are kept whenever
 * they appear, so the band's buttons come back for a deploy read later.
 */
export function afterOutput(d: Deploy | null, o: Outcome, now: number): { deploy: Deploy | null; toast: string | null } {
  if (!o.apiUrl && !o.revision && !o.failure && !o.siteUrl) return { deploy: d, toast: null }
  const base: Deploy = d ?? beginDeploy('deployed', now, null)
  const kept = { ...base, apiUrl: o.apiUrl ?? base.apiUrl, siteUrl: o.siteUrl ?? base.siteUrl }

  if (UP.has(base.stage) && o.failure) {
    return { deploy: { ...kept, stage: 'failed', stageAt: now, failure: o.failure }, toast: `Deploy failed: ${o.failure}` }
  }
  if (UP.has(base.stage) && o.revision !== null) {
    return {
      deploy: { ...kept, stage: 'starting', stageAt: now, revision: o.revision },
      toast: `Deployed revision ${o.revision} to Reboot Cloud`,
    }
  }
  if (base.stage === 'publish' && o.siteUrl) {
    return { deploy: { ...kept, stage: 'published', stageAt: now }, toast: 'Frontend published' }
  }

  return { deploy: d === null && !o.apiUrl && !o.siteUrl ? null : kept, toast: null }
}

/** `1m 12s`, `45s`. */
export function elapsed(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000))

  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`
}

/** The band's line for a running deploy. */
export function deployLine(d: Deploy, now: number): string {
  const what: Record<DeployStage, string> = {
    checking: 'Deploying to Reboot Cloud: checking permissions',
    build: 'Deploying to Reboot Cloud: building the image',
    push: 'Deploying to Reboot Cloud: pushing the image',
    rollout: 'Deploying to Reboot Cloud: rolling out the new revision',
    starting: `Deploying to Reboot Cloud: revision ${d.revision ?? ''} is starting up`.replace('  ', ' '),
    publish: 'Publishing the frontend to Cloudflare Pages',
    live: 'Live on Reboot Cloud',
    deployed: 'Deployed to Reboot Cloud',
    published: 'Frontend published',
    failed: `Deploy failed: ${d.failure ?? ''}`,
  }

  // A failed deploy's time stops where it failed.
  const end = d.stage === 'failed' ? d.stageAt : now

  return `${what[d.stage]} · ${elapsed(end - d.startedAt)}`
}

/** The `$.store` key holding a project's deployed URLs across sessions. */
export const deployKey = (root: string): string => `deploy:${root}`

/**
 * The latest Reboot Cloud and site URLs a project's `deploy/ledger.jsonl`
 * records. `scripts/deploy.sh` writes a line only after a deploy
 * succeeded, so these are the deployed app's, not ones a log mentions.
 */
export function ledgerUrls(text: string | null): { apiUrl: string | null; siteUrl: string | null } {
  let apiUrl: string | null = null
  let siteUrl: string | null = null
  for (const line of (text ?? '').split('\n')) {
    if (!line.trim()) continue
    try {
      const row = JSON.parse(line) as { api_url?: unknown; site?: unknown }
      if (typeof row.api_url === 'string' && row.api_url) apiUrl = row.api_url
      if (typeof row.site === 'string' && row.site) siteUrl = row.site
    } catch {
      continue
    }
  }
  return { apiUrl, siteUrl }
}

/** How often a deployed link is checked while the band runs. */
export const LINK_CHECK_MS = 60 * 1000

/** How many failed checks in a row take a shown link away. */
export const LINK_STRIKES = 2

/** What the checks know of one deployed link. */
export type LinkProbe = { ok: boolean; failures: number; checkedAt: number }

/** Whether a link is due a check: never checked, or not for a while. */
export const isProbeDue = (p: LinkProbe | undefined, now: number): boolean =>
  p === undefined || now - p.checkedAt >= LINK_CHECK_MS

/**
 * A link after a check. It shows only once it has answered; a shown link
 * survives one failed check (a blip) and goes after LINK_STRIKES in a row.
 */
export function afterProbe(p: LinkProbe | undefined, answered: boolean, now: number): LinkProbe {
  const failures = answered ? 0 : (p?.failures ?? 0) + 1
  return { ok: answered || (p?.ok === true && failures < LINK_STRIKES), failures, checkedAt: now }
}

/** Whether checks have given up on a link that never answered: one to forget. */
export const isDead = (p: LinkProbe | undefined): boolean => p !== undefined && !p.ok && p.failures >= LINK_STRIKES

/** The address that says whether a deployed link answers: the app's inspect page, the site itself. */
export const probeTarget = (kind: 'cloud' | 'site', url: string): string =>
  kind === 'cloud' ? `${url.replace(/\/+$/, '')}/__/inspect` : url
