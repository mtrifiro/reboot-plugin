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

/** How long a revision may answer 503 before the band stops waiting on it. */
export const STARTING_MS = 5 * 60 * 1000

/** What the process list shows of a deploy. */
export type Seen = { isUp: boolean; isBuild: boolean; isPush: boolean; isPublish: boolean }

/** A deploy's processes in `ps -axo command=` output. */
export function seenIn(ps: string): Seen {
  const lines = ps.split('\n')
  const has = (re: RegExp) => lines.some(l => re.test(l))

  return {
    isUp: has(/\brbt\s+cloud\s+up\b/),
    isBuild: has(/\bdocker\b.*\s(build|buildx\s+build)\s/),
    isPush: has(/\bdocker\b.*\spush\s/),
    isPublish: has(/\bwrangler\b.*\bpages\s+deploy\b/),
  }
}

/** A new deploy at `stage`, keeping the URLs of the one before. */
export const beginDeploy = (stage: DeployStage, now: number, was: Deploy | null): Deploy => ({
  stage,
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
  if (!active && seen.isUp) return beginDeploy(seen.isPush ? 'push' : seen.isBuild ? 'build' : 'checking', now, d)
  if (!active && seen.isPublish) return beginDeploy('publish', now, d)
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
  const site = text.match(/https:\/\/[\w.-]+\.pages\.dev\b/)

  return {
    apiUrl: api ? api[1]!.replace(/\/+$/, '') : null,
    revision: revision ? Number(revision[1]) : null,
    failure: failed ? failed[1]!.trim() : null,
    siteUrl: site ? `${site[0]}/` : null,
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

  return `${what[d.stage]} · ${elapsed(now - d.startedAt)}`
}

/** The `$.store` key holding a project's deployed URLs across sessions. */
export const deployKey = (root: string): string => `deploy:${root}`
