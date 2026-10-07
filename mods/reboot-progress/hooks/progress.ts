// Pure logic: which build step a tool call shows, and how the status
// line reads. Kept free of `$` so the tests can call it directly.

export const STEPS = [
  'Design',
  'API',
  'Shell',
  'Servicer',
  'Authorizers',
  'Frontend',
  'Tests',
  'Run',
] as const

export const RUN = STEPS.length - 1

// The skills that start (or re-enter) the build flow.
const BUILD_SKILL = /^(reboot:)?(app|build|mcp-ui|web-app)$/

export type Call =
  | { tool: 'Skill'; skill: string }
  | { tool: 'Bash'; command: string }
  | { tool: 'Write' | 'Edit'; file_path: string; text: string }

export const isBuildSkill = (skill: string): boolean => BUILD_SKILL.test(skill)

/**
 * The build step a call is evidence of, or null when it says nothing.
 * Paths follow the layouts in the mcp-ui and web-app skills.
 */
export function stepOf(call: Call): number | null {
  if (call.tool === 'Skill') {
    return isBuildSkill(call.skill) ? 0 : null
  }
  if (call.tool === 'Bash') {
    const c = call.command
    if (/\brbt\s+dev\s+run\b/.test(c)) return 7
    if (/\bpytest\b|\.feature\b/.test(c)) return 6
    if (/\bcopy\.sh\b|\brbt\s+generate\b|\buv\s+sync\b/.test(c)) return 2
    return null
  }
  const p = call.file_path
  // Generated code is never evidence of a step.
  if (/_rbt\.py$|\/node_modules\/|\/dist\//.test(p)) return null
  if (/\/tests\/[^/]*(\.feature|_test\.py)$/.test(p)) return 6
  if (/\/backend\/src\/servicers\/[^/]+\.py$/.test(p)) {
    return /\bdef authorizer\s*\(/.test(call.text) ? 4 : 3
  }
  if (/\/backend\/src\/(main|example_prompts)\.py$/.test(p)) return 2
  if (/\/(frontend|web)\/(?!(.*\/)?api\/)/.test(p)) return 5
  if (/\/api\/[^/]+\/v1\/[^/]+\.py$/.test(p) && !/\/(backend|frontend|web)\//.test(p)) {
    return 1
  }
  return null
}

export type Health = {
  backend: boolean
  frontend: boolean | null // null: the app has no frontend
  tunnel: boolean | null // null: not an MCP app, so no tunnel
  url: string | null
}

const dot = (isUp: boolean) => (isUp ? '●' : '○')

export function formatStatus(h: Health): string {
  const parts = [`rbt ${dot(h.backend)}`]
  if (h.frontend !== null) parts.push(`web ${dot(h.frontend)}`)
  if (h.tunnel !== null) parts.push(`tunnel ${dot(h.tunnel)}`)
  const line = parts.join('  ')

  return h.url ? `${line}  ${h.url}` : line
}

/** Ports in LISTEN state from `lsof -nP -iTCP -sTCP:LISTEN` output. */
export function listeningPorts(lsof: string): Set<number> {
  const ports = new Set<number>()
  for (const m of lsof.matchAll(/:(\d+) \(LISTEN\)/g)) ports.add(Number(m[1]))

  return ports
}

/** The backend port: `dev run --port=N` in `.rbtrc`, else 9991. */
export function backendPort(rbtrc: string): number {
  const m = rbtrc.match(/^\s*dev run\s+--port[= ](\d+)/m)

  return m ? Number(m[1]) : 9991
}

/** The cloudflared metrics port from a `ps` command line, else null. */
export function metricsPort(ps: string): number | null {
  const line = ps.split('\n').find(l => /cloudflared/.test(l) && /\btunnel\b/.test(l))
  if (!line) return null
  const m = line.match(/--metrics[= ](?:[\w.]+)?:(\d+)/)

  return m ? Number(m[1]) : 4040
}
