import { describe, expect, test } from 'claude-code/testing'

import {
  advanceTask,
  appLinks,
  asTask,
  backendPort,
  barRuns,
  barWidth,
  beginTask,
  commandKind,
  describeTask,
  finishTurn,
  formatStatus,
  listeningPorts,
  metricsPort,
  progressBar,
  skillKind,
  stepOf,
  taskAfterPrompt,
  taskLabel,
} from './progress'
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
    expect(appLinks(ports(9871), { backendPort: 9991, vitePort: 5273, hasWebApp: true }).dashboard).toBe(
      'http://127.0.0.1:9871/',
    )
    expect(appLinks(ports(), { backendPort: 9991, vitePort: 5273, hasWebApp: true }).dashboard).toBe(null)
  })

  test("a web app's page, or an MCP UI's setup wizard, while it serves", () => {
    expect(appLinks(ports(5273), { backendPort: 9991, vitePort: 5273, hasWebApp: true }).app).toBe(
      'http://localhost:5273/',
    )
    expect(appLinks(ports(9991), { backendPort: 9991, vitePort: 5273, hasWebApp: true }).app).toBe(null)
    expect(appLinks(ports(9991), { backendPort: 9991, vitePort: 4444, hasWebApp: false }).app).toBe(
      'http://localhost:9991/',
    )
  })
})

describe('status line', () => {
  test('formats each process the app has', () => {
    expect(formatStatus({ backend: true, frontend: false, tunnel: null, url: null })).toBe('rbt ●  web ○')
    expect(
      formatStatus({ backend: true, frontend: true, tunnel: true, url: 'https://a.trycloudflare.com' }),
    ).toBe('rbt ●  web ●  tunnel ●  https://a.trycloudflare.com')
  })

  test('reads ports from lsof, .rbtrc and ps', () => {
    const lsof = 'Python 1 me 3u IPv4 0t0 TCP 127.0.0.1:9991 (LISTEN)\nnode 2 me 4u IPv6 0t0 TCP [::1]:4444 (LISTEN)'
    expect([...listeningPorts(lsof)]).toEqual([9991, 4444])
    expect(backendPort('dev run --python\n')).toBe(9991)
    expect(backendPort('dev run --port=9100\n')).toBe(9100)
    expect(metricsPort('cloudflared tunnel --metrics localhost:4041 --url http://localhost:9991')).toBe(4041)
    expect(metricsPort('/usr/bin/zsh')).toBe(null)
  })
})

describe('progress bar', () => {
  test('a build fills over six phases, the current one half', () => {
    expect(progressBar(at('build', 0), 12)).toEqual({ filled: 1, empty: 11 })
    // Data model and setup are one phase, as are backend and access rules.
    expect(progressBar(at('build', 2), 12)).toEqual({ filled: 3, empty: 9 })
    expect(progressBar(at('build', 4), 12)).toEqual({ filled: 5, empty: 7 })
    expect(progressBar(at('build', 7), 12)).toEqual({ filled: 11, empty: 1 })
    expect(progressBar(at('build', 7, { isDone: true }), 12)).toEqual({ filled: 12, empty: 0 })
  })

  test('a feature fills over five phases, a fix over three', () => {
    expect(progressBar(at('feature', 3), 10)).toEqual({ filled: 5, empty: 5 })
    expect(progressBar(at('feature', 6), 10)).toEqual({ filled: 9, empty: 1 })
    // A fix: finding the cause, fixing it (any code), testing it.
    expect(progressBar(at('fix', 0), 12)).toEqual({ filled: 2, empty: 10 })
    expect(progressBar(at('fix', 5), 12)).toEqual({ filled: 6, empty: 6 })
    expect(progressBar(at('fix', 6), 12)).toEqual({ filled: 10, empty: 2 })
  })

  test('sizes to two-thirds of the room beside its labels, 8 to 48 cells', () => {
    expect(barWidth(20)).toBe(8)
    expect(barWidth(80)).toBe(37)
    expect(barWidth(200)).toBe(48)
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

  test('the bold label before the bar names the kind of work', () => {
    expect(taskLabel(at('build', 3))).toBe('Building')
    expect(taskLabel(at('feature', 3))).toBe('Adding Feature')
    expect(taskLabel(at('fix', 3))).toBe('Fixing')
    expect(taskLabel(at('fix', 6, { isDone: true }))).toBe('Done')
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

describe('bar colors', () => {
  test('orange at the left end, green at the right', () => {
    const full = barRuns(10, 10)
    expect(full[0]!.color).toBe('#f97415') // orange
    expect(full[full.length - 1]!.color).toBe('#21c45d') // green
    // Through yellow, not olive: the middle cell is bright.
    expect(full[4]!.color).toBe('#ace814')
    expect(full.reduce((n, r) => n + r.cells, 0)).toBe(10)
  })

  test('a short fill stays at the orange end', () => {
    const short = barRuns(2, 20)
    expect(short[0]!.color).toBe('#f97415')
    expect(short.reduce((n, r) => n + r.cells, 0)).toBe(2)
    expect(barRuns(0, 20)).toEqual([])
  })
})
