import { describe, expect, test } from 'claude-code/testing'

import {
  asBuild,
  backendPort,
  barWidth,
  formatStatus,
  listeningPorts,
  metricsPort,
  nextBuild,
  progressBar,
  stepOf,
} from './progress'

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
    expect(write('tests/add.feature')).toBe(6)
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
  test('fills with the steps done', () => {
    expect(progressBar(0, false, 16)).toEqual({ filled: 0, empty: 16, label: 'Design · 1 of 8' })
    expect(progressBar(3, false, 16)).toEqual({ filled: 6, empty: 10, label: 'Servicer · 4 of 8' })
    expect(progressBar(7, true, 16)).toEqual({ filled: 16, empty: 0, label: 'Done · 8 of 8' })
  })

  test('sizes to the band, 10 to 30 cells', () => {
    expect(barWidth(40)).toBe(10)
    expect(barWidth(60)).toBe(22)
    expect(barWidth(200)).toBe(30)
  })
})

describe('build state', () => {
  test('a build skill opens a build unless one is under way', () => {
    expect(nextBuild(null, 0, true)).toEqual({ step: 0, isDone: false })
    expect(nextBuild({ step: 3, isDone: false }, 0, true)).toEqual({ step: 3, isDone: false })
    expect(nextBuild({ step: 7, isDone: true }, 0, true)).toEqual({ step: 0, isDone: false })
  })

  test('evidence starts a build a resumed session never saw open', () => {
    expect(nextBuild(null, 3, false)).toEqual({ step: 3, isDone: false })
    // Running a finished app is not a build.
    expect(nextBuild(null, 7, false)).toBe(null)
  })

  test('evidence moves forward only, and Run finishes', () => {
    expect(nextBuild({ step: 4, isDone: false }, 2, false)).toEqual({ step: 4, isDone: false })
    expect(nextBuild({ step: 4, isDone: false }, 7, false)).toEqual({ step: 7, isDone: true })
    expect(nextBuild({ step: 7, isDone: true }, 3, false)).toEqual({ step: 7, isDone: true })
  })

  test('only a well-formed stored build is restored', () => {
    expect(asBuild({ step: 2, isDone: false })).toEqual({ step: 2, isDone: false })
    expect(asBuild({ step: 99, isDone: false })).toBe(null)
    expect(asBuild('nonsense')).toBe(null)
    expect(asBuild(undefined)).toBe(null)
  })
})
