import { describe, expect, test } from 'claude-code/testing'

import {
  advanceTask,
  appLinks,
  asTask,
  backendPort,
  dashboardPort,
  beginTask,
  commandKind,
  describeTask,
  finishTurn,
  listeningPorts,
  vitePortOf,
  observe,
  skillKind,
  stepOf,
  taskAfterPrompt,
  STOP_POLLS,
  UNWATCHED,
} from './progress'
import type { Watch } from './progress'
import type { Task, TaskKind } from './progress'

const at = (kind: TaskKind, step: number, extra: Partial<Task> = {}): Task => ({
  kind,
  step,
  isDone: false,
  ...extra,
})

const P = '/work/todo-list'
const write = (path: string, text = '') => stepOf({ tool: 'Write', file_path: `${P}/${path}`, text })
const bash = (command: string) => stepOf({ tool: 'Bash', command })

describe('stepOf', () => {
  test('build skills open the Design step', () => {
    expect(stepOf({ tool: 'Skill', skill: 'reboot:build' })).toBe(0)
    expect(stepOf({ tool: 'Skill', skill: 'reboot:web-app' })).toBe(0)
    expect(stepOf({ tool: 'Skill', skill: 'reboot:run' })).toBe(null)
  })

  test('paths map to the build steps', () => {
    expect(write('api/todo_list/v1/todo_list.py')).toBe(1)
    expect(write('backend/src/main.py')).toBe(2)
    expect(write('backend/src/servicers/todo_list.py', 'async def add(self): ...')).toBe(3)
    expect(write('backend/src/servicers/todo_list.py', 'def authorizer(self):')).toBe(4)
    expect(write('frontend/mcp/board/App.tsx')).toBe(5)
    expect(write('web/src/pages/Home.tsx')).toBe(5)
    expect(write('tests/todo_list_test.py')).toBe(6)
    // The spec, written right after Planning, is not Tests.
    expect(write('tests/add.feature')).toBe(null)
  })

  test('generated code is not evidence', () => {
    expect(write('backend/api/todo_list/v1/todo_list_rbt.py')).toBe(null)
    expect(write('frontend/api/todo_list/v1/todo_list_rbt_react.ts')).toBe(null)
    expect(write('web/src/api/todo_list/v1/todo_list_rbt_web.ts')).toBe(null)
  })

  test('commands map to the build steps', () => {
    expect(bash('uv run rbt generate')).toBe(2)
    expect(bash('uv run pytest tests')).toBe(6)
    expect(bash('uv run rbt dev run --no-chaos')).toBe(7)
    expect(bash('ls')).toBe(null)
  })
})

describe('links', () => {
  const ports = (...p: number[]) => new Set(p)

  test('the dashboard, while it listens', () => {
    expect(appLinks(ports(9871), { backendPort: 9991, dashboardPort: 9871, vitePort: 5273, hasWebApp: true }).dashboard).toBe(
      'http://127.0.0.1:9871/',
    )
    expect(appLinks(ports(), { backendPort: 9991, dashboardPort: 9871, vitePort: 5273, hasWebApp: true }).dashboard).toBe(null)
    // Another project's dashboard on the default port is not this one's.
    expect(appLinks(ports(9871), { backendPort: 9991, dashboardPort: 9872, vitePort: 5273, hasWebApp: true }).dashboard).toBe(null)
  })

  test("the dashboard's port is the project's .rbtrc's", () => {
    expect(dashboardPort('dev run --python\n')).toBe(9871)
    expect(dashboardPort('dev run --dashboard-port=9881\n')).toBe(9881)
    expect(dashboardPort('dev run --dashboard-port=9872\ndashboard --port=9873\n')).toBe(9873)
  })

  test("Vite's port is the one this project's Vite listens on", () => {
    const ps = [
      '  101 node /w/other/web/node_modules/.bin/vite',
      '  102 node /w/app/web/node_modules/.bin/vite',
      '  103 /w/app/.venv/bin/python -m reboot.dashboard.backend.main',
      '  104 node /w/app/web/node_modules/.bin/vite --port 59198 --strictPort',
      '  105 node /w/app/web/node_modules/.bin/vite preview --port 4273',
    ].join('\n')
    const lsof = [
      'node 101 me 23u IPv6 0xa 0t0 TCP [::1]:5273 (LISTEN)',
      'node 102 me 23u IPv6 0xb 0t0 TCP [::1]:5275 (LISTEN)',
      'node 102 me 24u IPv6 0xc 0t0 TCP [::1]:24678 (LISTEN)',
      'node 104 me 23u IPv6 0xd 0t0 TCP *:59198 (LISTEN)',
      'node 105 me 23u IPv6 0xe 0t0 TCP *:4273 (LISTEN)',
    ].join('\n')
    expect(vitePortOf(lsof, ps, '/w/app')).toBe(5275)
    expect(vitePortOf(lsof, ps, '/w/none')).toBe(null)
    // Only a test suite's Vite and a preview: no dev server to open.
    expect(vitePortOf(lsof, ps.replace(/^ {2}102 .*$/m, ''), '/w/app')).toBe(null)
  })

  test("a web app's page, or an MCP UI's setup wizard, while it serves", () => {
    expect(appLinks(ports(5273), { backendPort: 9991, dashboardPort: 9871, vitePort: 5273, hasWebApp: true }).app).toBe(
      'http://localhost:5273/',
    )
    expect(appLinks(ports(9991), { backendPort: 9991, dashboardPort: 9871, vitePort: null, hasWebApp: true }).app).toBe(null)
    expect(appLinks(ports(9991), { backendPort: 9991, dashboardPort: 9871, vitePort: 4444, hasWebApp: false }).app).toBe(
      'http://localhost:9991/',
    )
  })
})

describe('ports', () => {
  test('reads ports from lsof, .rbtrc and ps', () => {
    const lsof = 'Python 1 me 3u IPv4 0t0 TCP 127.0.0.1:9991 (LISTEN)\nnode 2 me 4u IPv6 0t0 TCP [::1]:4444 (LISTEN)'
    expect([...listeningPorts(lsof)]).toEqual([9991, 4444])
    expect(backendPort('dev run --python\n')).toBe(9991)
    expect(backendPort('dev run --port=9100\n')).toBe(9100)
  })
})

describe('what starts a task', () => {
  test('skills and typed slash commands name a kind', () => {
    expect(skillKind('reboot:app')).toBe('build')
    expect(skillKind('reboot:web-app')).toBe('build')
    expect(skillKind('reboot:feature')).toBe('feature')
    expect(skillKind('reboot:run')).toBe(null)
    expect(commandKind('/reboot:app build a user friendly interface to Google Analytics')).toBe('build')
    expect(commandKind('  /reboot:feature add transfers')).toBe('feature')
    expect(commandKind('/reboot:run')).toBe(null)
    expect(commandKind('/app build it')).toBe(null)
    expect(commandKind('please /reboot:app')).toBe(null)
  })

  test('a skill starts a task unless one is under way in this session', () => {
    expect(beginTask(null, 'build')).toEqual(at('build', 0))
    // The build flow calls the feature skill for its spec: still the build.
    expect(beginTask(at('build', 1), 'feature')).toEqual(at('build', 1))
    expect(beginTask(at('build', 7, { isDone: true }), 'feature')).toEqual(at('feature', 0))
    expect(beginTask(at('build', 6, { isRestored: true }), 'build')).toEqual(at('build', 0))
  })

  test('a prompt for new work starts a task; a follow-up keeps it', () => {
    const building = at('build', 3)
    expect(taskAfterPrompt(building, 'same')).toBe(building)
    expect(taskAfterPrompt(building, null)).toBe(building)
    // "yes, build it" read as new work of the same kind: keep the build.
    expect(taskAfterPrompt(building, 'build')).toBe(building)
    // A different kind of work: a new task.
    expect(taskAfterPrompt(building, 'fix')).toEqual(at('fix', 0))
    // A finished task stays, Done, through follow-ups ("continue").
    const done = at('feature', 6, { isDone: true })
    expect(taskAfterPrompt(done, 'same')).toBe(done)
    // After a finished task, or with none, new work of any kind starts one.
    expect(taskAfterPrompt(at('feature', 6, { isDone: true }), 'feature')).toEqual(at('feature', 0))
    expect(taskAfterPrompt(null, 'feature')).toEqual(at('feature', 0))
  })

  test('the current task is described for the summary', () => {
    expect(describeTask(null)).toBe('none')
    expect(describeTask(at('fix', 3))).toBe('fixing a bug, at the backend step')
    expect(describeTask(at('build', 7, { isDone: true }))).toBe('none')
  })
})

describe('how a task moves', () => {
  test('evidence moves a task forward only, and starts none', () => {
    expect(advanceTask(at('build', 4), 2)).toEqual(at('build', 4))
    expect(advanceTask(at('build', 1), 3)).toEqual(at('build', 3))
    expect(advanceTask(null, 3)).toBe(null)
    expect(advanceTask(at('build', 7, { isDone: true }), 3)).toEqual(at('build', 7, { isDone: true }))
  })

  test("a build's tests count once the backend exists, Launch once the screens do", () => {
    // The spec's test module, or the @wip spec run, right after planning.
    expect(advanceTask(at('build', 1), 6)).toEqual(at('build', 1))
    expect(advanceTask(at('build', 3), 6)).toEqual(at('build', 6))
    // The servers started mid-build to check the backend.
    expect(advanceTask(at('build', 3), 7)).toEqual(at('build', 3))
    expect(advanceTask(at('build', 5), 7)).toEqual(at('build', 7))
  })

  test("a feature or fix tests once it changed code, and Launch after its tests", () => {
    expect(advanceTask(at('fix', 0), 6)).toEqual(at('fix', 0))
    expect(advanceTask(at('fix', 3), 6)).toEqual(at('fix', 6))
    expect(advanceTask(at('feature', 5), 7)).toEqual(at('feature', 5))
    expect(advanceTask(at('feature', 6), 7)).toEqual(at('feature', 7))
  })

  test('a task restored from an earlier session takes the first evidence as true', () => {
    expect(advanceTask(at('build', 6, { isRestored: true }), 5)).toEqual(at('build', 5))
  })

  test('a turn that ends at the last step finishes the task', () => {
    expect(finishTurn(at('build', 7))).toEqual(at('build', 7, { isDone: true }))
    expect(finishTurn(at('build', 6))).toEqual(at('build', 6))
    expect(finishTurn(at('fix', 6))).toEqual(at('fix', 6, { isDone: true }))
    expect(finishTurn(at('feature', 5))).toEqual(at('feature', 5))
    expect(finishTurn(null)).toBe(null)
  })

  test('a stored task is restored; one stored before kinds is a build', () => {
    expect(asTask({ kind: 'fix', step: 3, isDone: false })).toEqual(at('fix', 3))
    expect(asTask({ step: 2, isDone: false })).toEqual(at('build', 2))
    expect(asTask({ step: 99, isDone: false })).toBe(null)
    expect(asTask('nonsense')).toBe(null)
  })
})

describe('start and stop toasts', () => {
  /** The changes a series of polls announces. */
  const changes = (polls: boolean[]) => {
    let w: Watch = UNWATCHED
    return polls.map(isUp => {
      const r = observe(w, isUp)
      w = r.watch
      return r.change
    })
  }

  test('the first poll only learns the state', () => {
    expect(changes([true])).toEqual([null])
    expect(changes([false])).toEqual([null])
  })

  test('a start is announced at once', () => {
    expect(changes([false, true])).toEqual([null, 'started'])
  })

  test('a stop is announced once it lasts', () => {
    const down = Array(STOP_POLLS).fill(false)
    expect(changes([true, ...down]).at(-1)).toBe('stopped')
    // Then a start again.
    expect(changes([true, ...down, true]).at(-1)).toBe('started')
  })

  test('a restart on save is not announced', () => {
    expect(changes([true, false, false, true, false, true])).toEqual([null, null, null, null, null, null])
  })
})
