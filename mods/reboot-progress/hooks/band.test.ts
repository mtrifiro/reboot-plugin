import { expect, mock, test } from 'claude-code/testing'

const PLUGIN = 'reboot-progress'

// The test runtime has timers; the hooks module's typings don't declare them.
const wait = (ms: number) =>
  new Promise<void>(resolve =>
    (globalThis as unknown as { setTimeout: (f: () => void, ms: number) => void }).setTimeout(resolve, ms),
  )
const BAND = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 120 }

/** The band's heading: Reboot Status on the terminal, which has no logo; Status elsewhere. */
const HEADING = (surface: string) => (surface === 'terminal' ? /^Reboot Status$/ : /^Status$/)

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the band follows the build on ${surface}`, async ($, on) => {
    // Stand in for the engine beneath: every tool call succeeds.
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('fs.exists', () => ({ value: false }) as never)
    on('clock.now', () => ({ value: 1000 }) as never)
    // The engine's own band is empty.
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })

    const empty = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect(await empty.findAll({ text: /Reboot/ })).toEqual([])
    await empty.unmount()

    await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
    await $.tool.call({ tool: 'Write', file_path: '/w/app/api/app/v1/app.py', content: '' })

    // The data model is Design; the Now line says so. (Matched as a string:
    // a RegExp with a non-ASCII character does not survive the kit's transport.)
    const designing = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await designing.findAll({ type: 'Text', text: 'Design \u00b7 ' })).length).toBe(1)
    await designing.unmount()

    await $.tool.call({
      tool: 'Write',
      file_path: '/w/app/backend/src/servicers/app.py',
      content: 'def authorizer(self): ...',
    })

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    // A static Status heading: neither the kind of work nor the step.
    expect((await band.findAll({ type: 'Text', text: HEADING(surface) })).length).toBe(1)
    expect(await band.findAll({ type: 'Text', text: /^(Building|Adding Feature|Fixing|Done)$/ })).toEqual([])
    expect(await band.findAll({ type: 'Text', text: /access rules|backend|screens/ })).toEqual([])
    // The servicers are Prove.
    expect((await band.findAll({ type: 'Text', text: 'Prove \u00b7 ' })).length).toBe(1)
    // No progress bar: the task's name alone.
    expect(await band.findAll({ type: 'Text', text: /█|░/ })).toEqual([])

    await $.command.run({ command: 'reboot-progress', args: 'hide' } as never)
    expect(await band.findAll({ text: /Reboot/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the activity columns draw on ${surface}`, async ($, on) => {
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    // The model names the task; the prompt goes through.
    on('model.complete', () => ({ value: { isAnswered: true, text: 'Writing the servicers\nWrote the servicers' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: 'Write the servicers for the app, then the tests.' } as never)
    await wait(50) // the summary runs in the background

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: 'Writing the servicers' })).length).toBe(1)
    // The status alone, with no Now heading over it.
    expect(await band.findAll({ type: 'Text', text: /^Now$/ })).toEqual([])
    expect(await band.findAll({ type: 'Text', text: /Just completed/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a typed /reboot:app shows the band at once on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('model.complete', () => ({ value: { isAnswered: true, text: 'NOW: Planning the dashboard\nDONE: NONE' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: '/reboot:app build a user friendly interface to Google Analytics' } as never)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /Reboot/ })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: HEADING(surface) })).length).toBe(1)
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a prompt the summary calls a fix shows its Now on ${surface}`, async ($, on) => {
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('model.complete', () =>
      ({ value: { isAnswered: true, text: 'NOW: Fixing the sign-in button\nDONE: NONE\nTASK: NEW FIX' } }) as never,
    )
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: 'The sign-in button does nothing when I click it.' } as never)
    await wait(50) // the summary runs in the background

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /Reboot/ })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: 'Fixing the sign-in button' })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: HEADING(surface) })).length).toBe(1)
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the Dashboard button opens the dashboard in the browser on ${surface}`, async ($, on) => {
    const opened: string[][] = []
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('fs.read', () => ({ value: '' }) as never)
    on('ui.status', () => ({ value: undefined }) as never)
    on('process.run', ($, e) => {
      const argv = (e as { argv: string[] }).argv
      if (argv[0] === 'open') opened.push(argv)
      const stdout = argv[0] === 'lsof' ? 'rbt 1 me 3u IPv4 0t0 TCP 127.0.0.1:9871 (LISTEN)' : ''
      return { value: { exitCode: 0, stdout, stderr: '' } } as never
    })

    // Starting the app checks what is serving, which finds the dashboard.
    await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
    await wait(50)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    // Its address waits, hidden, for the pointer on the button.
    expect((await band.findAll({ type: 'Text', text: /^ ?Opens the dashboard: http:\/\/127\.0\.0\.1:9871\/$/ })).length).toBe(1)
    await band.press({ key: 'dashboard' })
    expect(opened).toEqual([['open', 'http://127.0.0.1:9871/']])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`Now leaves "Idle" the moment a prompt is sent on ${surface}`, async ($, on) => {
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    // The summary never comes back: Now must still not wait.
    on('model.complete', () => ({ value: { isAnswered: false, reason: 'empty-reply' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)

    await $.prompt.submit({ text: "let's add the YOY feature" } as never)

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect(await band.findAll({ type: 'Text', text: /^Idle$/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the review table holds the band at the checkpoint until the person answers on ${surface}`, async ($, on) => {
    const toasts: string[] = []
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('ui.toast', ($, e) => {
      toasts.push((e as { text: string }).text)
      return { value: undefined } as never
    })
    on('model.complete', () => ({ value: { isAnswered: false, reason: 'empty-reply' } }) as never)
    on('prompt.submit', ($, e) => ({ text: e.text }) as never)
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('clock.now', () => ({ value: 1000 }) as never)

    await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
    await $.session.append({
      message: {
        type: 'assistant',
        content: [
          {
            type: 'text',
            text: 'Here is the design.\n\n| State type | State ID | Rule | Method | Kind | Who may call | Scenario |\n| --- | --- | --- | --- | --- | --- | --- |\n| `Room` | room number | booked once per night | `book` | Writer | the app | "A second guest" |\n',
          },
        ],
      },
      door: 'response',
      origin: { kind: 'model', model: 'test' },
      uuid: 'review-1',
    } as never)

    const waiting = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await waiting.findAll({ type: 'Text', text: 'Design \u00b7 awaiting your acceptance' })).length).toBe(1)
    expect(toasts).toEqual(['The design, for your review'])
    await waiting.unmount()

    // The person's answer, whatever it is, ends the wait.
    await $.prompt.submit({ text: 'Looks right, go ahead.' } as never)
    const answered = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect(await answered.findAll({ type: 'Text', text: /awaiting your acceptance/ })).toEqual([])
  })
}

test('the Reboot logo draws beside Reboot where the surface has Svg; the terminal says Reboot Status', async ($, on) => {
  on('fs.exists', () => ({ value: false }) as never)
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })

  const desktop = await $.ui.mount({ plugin: PLUGIN, surface: 'desktop', component: 'AbovePrompt', props: BAND as never })
  expect((await desktop.findAll({ type: 'Svg' })).length).toBe(1)
  const terminal = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await terminal.findAll({ type: 'Svg' })).toEqual([])
  // Where the logo can't draw, the heading names Reboot, in green, and
  // nothing sits at the right.
  const [heading] = await terminal.findAll({ type: 'Text', text: /^Reboot Status$/ })
  expect((heading as { props: { color?: string } }).props.color).toBe('success')
  expect(await terminal.findAll({ type: 'Text', text: /^(Reboot|Status)$/ })).toEqual([])
  // A rule after it to the right edge, on the terminal alone.
  expect((await terminal.findAll({ type: 'Text', text: /^─+$/ })).length).toBe(1)
  expect(await desktop.findAll({ type: 'Text', text: /^─+$/ })).toEqual([])
  // The app keeps Status on the left and the logo and Reboot on the right.
  expect((await desktop.findAll({ type: 'Text', text: /^Status$/ })).length).toBe(1)
  const [plain] = await desktop.findAll({ type: 'Text', text: /^Reboot$/ })
  expect((plain as { props: { color?: string } }).props.color).toBe(undefined)
})

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a deploy's output toasts and adds a Cloud button on ${surface}`, async ($, on) => {
    const toasts: string[] = []
    const opened: string[][] = []
    // The deployed app answers its link's check, before the check's own
    // five-second limit (which the test clock would otherwise reach at once).
    on('http.fetch', () => ({ value: { status: 200, ok: true, headers: {}, text: '' } }) as never)
    on('clock.sleep', () => new Promise(() => undefined) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('clock.now', () => ({ value: 1000 }) as never)
    on('ui.toast', ($, e) => {
      toasts.push((e as { text: string }).text)
      return { value: undefined } as never
    })
    on('process.run', ($, e) => {
      opened.push((e as { argv: string[] }).argv)
      return { value: { exitCode: 0, stdout: '', stderr: '' } } as never
    })
    on('tool.call', () =>
      ({
        result: {},
        text: "'app' revision 7 is available:\n\n  Your API is available at:      https://a1b2c3.c1.rbt.cloud:9991\n",
      }) as never,
    )

    await $.tool.call({ tool: 'Bash', command: 'uv run rbt cloud up --organization=acme' })

    expect(toasts).toEqual(['Deployed revision 7 to Reboot Cloud'])
    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    expect((await band.findAll({ type: 'Text', text: /Deploying to Reboot Cloud: revision 7 is starting up/ })).length).toBe(1)
    await band.press({ key: 'cloud' })
    expect(opened).toContainEqual(['open', 'https://a1b2c3.c1.rbt.cloud:9991'])
  })
}

for (const kind of ['an MCP UI', 'a web app serving MCP'] as const) {
  test(`${kind} deployed to Reboot Cloud gets an MCP button that opens its own connect page`, async ($, on) => {
    const opened: string[][] = []
    // The deployed app answers its link's check, before the check's own
    // five-second limit (which the test clock would otherwise reach at once).
    on('http.fetch', () => ({ value: { status: 200, ok: true, headers: {}, text: '' } }) as never)
    on('clock.sleep', () => new Promise(() => undefined) as never)
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)

      return h(Box, {}) as never
    })
    on('clock.now', () => ({ value: 1000 }) as never)
    on('session.cwd', () => ({ value: '/w/app' }) as never)
    const files = kind === 'an MCP UI' ? ['/w/app/.rbtrc', '/w/app/frontend/mcp'] : ['/w/app/.rbtrc']
    on('fs.exists', ($, e) => ({ value: files.includes((e as { path: string }).path) }) as never)
    on('fs.read', ($, e) => {
      const isMain = kind !== 'an MCP UI' && (e as { path: string }).path === '/w/app/backend/src/main.py'
      return { value: isMain ? 'Application(servicers=[], example_prompts=example_prompts)' : '' } as never
    })
    on('ui.status', () => ({ value: undefined }) as never)
    on('ui.toast', () => ({ value: undefined }) as never)
    on('process.run', ($, e) => {
      const argv = (e as { argv: string[] }).argv
      if (argv[0] === 'open') opened.push(argv)
      return { value: { exitCode: 0, stdout: '', stderr: '' } } as never
    })
    on('tool.call', () =>
      ({
        result: {},
        text: "'app' revision 7 is available:\n\n  Your API is available at:      https://a1b2c3.prod1.rbt.cloud:9991\n",
      }) as never,
    )

    await $.tool.call({ tool: 'Bash', command: 'uv run rbt cloud up --organization=acme' })
    // Starting the app polls, which finds that it serves MCP.
    await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
    await wait(50)

    const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
    expect(await band.findAll({ type: 'Button', text: /Cloud/ })).toEqual([])
    await band.press({ key: 'mcp' })
    expect(opened).toEqual([['open', 'https://a1b2c3.prod1.rbt.cloud/']])
  })
}

test('a turn waiting on tests in the foreground shows how long they have run', async ($, on) => {
  let release = () => {}
  const blocked = new Promise<void>(resolve => (release = resolve))
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: 1000 }) as never)
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.read', () => ({ value: '' }) as never)
  on('ui.status', () => ({ value: undefined }) as never)
  on('model.complete', () => ({ value: { isAnswered: false, reason: 'empty-reply' } }) as never)
  on('prompt.submit', ($, e) => ({ text: e.text }) as never)
  // The test run shows in ps, piped, so its output says nothing.
  on('process.run', () =>
    ({ value: { exitCode: 0, stdout: '  9 /w/app/.venv/bin/python /w/app/.venv/bin/pytest -m critical -q', stderr: '' } }) as never,
  )
  on('tool.call', async ($, e) => {
    if (/pytest/.test(String((e as { command?: string }).command))) await blocked
    return { result: {}, text: 'ok' } as never
  })

  await $.prompt.submit({ text: 'run the critical tests' } as never)
  // Starting the app polls, which finds the test run in ps.
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const tests = $.tool.call({ tool: 'Bash', command: 'timeout 900 uv run pytest -m critical -q 2>&1 | grep -E "passed|failed"' })
  await wait(50)

  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await band.findAll({ type: 'Text', text: 'Waiting for the tests to finish · 0s' })).length).toBe(1)
  release()
  await tests
  const after = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await after.findAll({ type: 'Text', text: /Waiting for the tests/ })).toEqual([])
})

test("between turns the band shows the run the project's runner records, and its result after", async ($, on) => {
  let file = JSON.stringify({
    started_at: '2026-10-08T11:24:00-05:00',
    finished_at: null,
    modules: [
      { name: 'accounts_test', status: 'passed', passed: 114, failed: 0, seconds: 130.1 },
      { name: 'web_test', status: 'running' },
    ],
  })
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: Date.parse('2026-10-08T11:30:00-05:00') }) as never)
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.read', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.reboot/test-run.json' ? file : '' }) as never)
  on('fs.stat', () => ({ value: { kind: 'file', size: 1, mtimeMs: Date.parse('2026-10-08T11:29:00-05:00') } }) as never)
  on('ui.status', () => ({ value: undefined }) as never)
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  on('process.run', () => ({ value: { exitCode: 0, stdout: '  9 /w/app/.venv/bin/pytest tests/web_test.py', stderr: '' } }) as never)

  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  // No history yet: how far, and no time.
  expect((await band.findAll({ type: 'Text', text: 'So far: 1 of 2 modules, 114 passed, 0 failed\nLeft: 1 module' })).length).toBe(1)

  file = file.replace('"finished_at":null', '"finished_at":"2026-10-08T11:31:00-05:00"').replace('"status":"running"', '"status":"failed","seconds":300')
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const after = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await after.findAll({ type: 'Text', text: /^Done: 2 modules, 114 passed, 1 failed \(web_test\)\nTook 7m 00s, finished at \d+:31$/ })).length).toBe(1)
})

test('a recorded run killed mid-way shows as stopped within seconds, not as still running', async ($, on) => {
  const file = JSON.stringify({
    started_at: '2026-10-08T11:24:00-05:00',
    finished_at: null,
    modules: [
      { name: 'accounts_test', status: 'passed', passed: 114, failed: 0, seconds: 130.1 },
      { name: 'web_test', status: 'running' },
    ],
  })
  let now = Date.parse('2026-10-08T11:30:00-05:00')
  let ps = '  9 /w/app/.venv/bin/pytest tests/web_test.py'
  // The store keeps when the band last saw the run in ps.
  const store = new Map<string, unknown>()
  on('store.get', ($, e) => ({ value: store.get((e as { key: string }).key) ?? null }) as never)
  on('store.set', ($, e) => {
    store.set((e as { key: string }).key, (e as { value: unknown }).value)
    return { value: undefined } as never
  })
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: now }) as never)
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.read', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.reboot/test-run.json' ? file : '' }) as never)
  on('fs.stat', () => ({ value: { kind: 'file', size: 1, mtimeMs: Date.parse('2026-10-08T11:29:00-05:00') } }) as never)
  on('ui.status', () => ({ value: undefined }) as never)
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  on('process.run', () => ({ value: { exitCode: 0, stdout: ps, stderr: '' } }) as never)

  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await band.findAll({ type: 'Text', text: 'So far: 1 of 2 modules, 114 passed, 0 failed\nLeft: 1 module' })).length).toBe(1)

  // Killed: gone from ps, and its file never got an end.
  ps = ''
  now += 20_000
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const after = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await after.findAll({ type: 'Text', text: /^Stopped: 1 of 2 modules, 114 passed, 0 failed\nRan 6m 00s, stopped at \d+:30$/ })).length).toBe(1)
  expect(await after.findAll({ type: 'Text', text: /So far/ })).toEqual([])
})

test('narration is summarized at most once per gap, and not while the band is hidden', async ($, on) => {
  let summaries = 0
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('fs.exists', () => ({ value: false }) as never)
  on('clock.now', () => ({ value: 1000 }) as never)
  // The booked slot never comes round within the test.
  on('clock.after', () => new Promise<never>(() => {}) as never)
  on('model.complete', () => {
    summaries++
    return { value: { isAnswered: true, text: 'NOW: Writing the servicers\nDONE: NONE' } } as never
  })
  on('prompt.submit', ($, e) => ({ text: e.text }) as never)
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  const narrate = (text: string, uuid: string) =>
    $.session.append({
      message: { type: 'assistant', content: [{ type: 'text', text }] },
      door: 'response',
      origin: { kind: 'model', model: 'test' },
      uuid,
    } as never)

  await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
  await narrate('Now writing the servicers for the rooms and the bookings, one method at a time.', 'n-1')
  await narrate('Now writing the authorizers for every servicer, the rules from the design.', 'n-2')
  await wait(50)
  expect(summaries).toBe(1)

  await $.command.run({ command: 'reboot-progress', args: 'hide' } as never)
  await narrate('Now running the scenarios red before any servicer body exists.', 'n-3')
  await $.prompt.submit({ text: 'Run the full suite and tell me what fails.' } as never)
  await wait(50)
  expect(summaries).toBe(1)
})

test('a session outside a Reboot project draws nothing and asks for no summary', async ($, on) => {
  let summaries = 0
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('session.cwd', () => ({ value: '/w/other' }) as never)
  on('fs.exists', () => ({ value: false }) as never)
  on('fs.list', () => ({ value: [] }) as never)
  on('model.complete', () => {
    summaries++
    return { value: { isAnswered: true, text: 'NOW: Fixing the button\nDONE: NONE\nTASK: NEW FIX' } } as never
  })
  on('prompt.submit', ($, e) => ({ text: e.text }) as never)

  await $.prompt.submit({ text: 'The sign-in button does nothing when I click it.' } as never)
  await wait(50)

  expect(summaries).toBe(0)
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await band.findAll({ text: /Reboot/ })).toEqual([])
})

test('a dry run of the deploy script, or a doc that mentions a site, starts no deploy', async ($, on) => {
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: 1000 }) as never)
  on('tool.call', ($, e) => {
    const command = String((e as { command?: string }).command)
    const text = /dry-run/.test(command) ? 'would deploy revision 8' : 'https://app.pages.dev serves the current build'
    return { result: {}, text } as never
  })

  await $.tool.call({ tool: 'Bash', command: 'scripts/deploy.sh --dry-run' })
  await $.tool.call({ tool: 'Bash', command: 'grep -n pages.dev docs/DEPLOYING.md' })

  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await band.findAll({ text: /Deploying|Site/ })).toEqual([])
})

test("a background deploy's output, read back, toasts and adds the Cloud button", async ($, on) => {
  const toasts: string[] = []
  // The deployed app answers its link's check, before the check's own
  // five-second limit (which the test clock would otherwise reach at once).
  on('http.fetch', () => ({ value: { status: 200, ok: true, headers: {}, text: '' } }) as never)
  on('clock.sleep', () => new Promise(() => undefined) as never)
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: 1000 }) as never)
  on('ui.toast', ($, e) => {
    toasts.push((e as { text: string }).text)
    return { value: undefined } as never
  })
  on('tool.call', ($, e) => {
    const text =
      (e as { tool: string }).tool === 'Bash'
        ? 'Command running in background with ID: b1\nOutput is being written to: /tmp/b1.output'
        : "'app' revision 9 is available:\n\n  Your API is available at:      https://d4e5f6.c1.rbt.cloud:9991\n"
    return { result: {}, text } as never
  })

  await $.tool.call({ tool: 'Bash', command: 'uv run rbt cloud up --organization=acme', run_in_background: true } as never)
  // Its process has exited by the time its output is read.
  await $.tool.call({ tool: 'Read', file_path: '/tmp/b1.output' })

  expect(toasts).toEqual(['Deployed revision 9 to Reboot Cloud'])
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await band.findAll({ type: 'Button', text: /Cloud/ })).length).toBe(1)
})

test('a deploy address that never answers shows no button, and is forgotten', async ($, on) => {
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  let now = 1000
  on('clock.now', () => ({ value: now }) as never)
  on('ui.toast', () => ({ value: undefined }) as never)
  // Nothing is deployed there: a test's or a log's made-up address.
  on('http.fetch', () => ({ value: { status: 404, ok: false, headers: {}, text: 'Not found' } }) as never)
  on('tool.call', () =>
    ({
      result: {},
      text: "'app' revision 7 is available:\n\n  Your API is available at:      https://a1b2c3.c1.rbt.cloud:9991\n  https://abc.app.pages.dev serves the current build\n",
    }) as never,
  )

  await $.tool.call({ tool: 'Bash', command: 'uv run rbt cloud up --organization=acme' })
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await band.findAll({ type: 'Button', text: /Cloud|Site/ })).toEqual([])
})

test("a Read of a Reboot skill's SKILL.md starts the task as the Skill call would, in a Reboot project only", async ($, on) => {
  let cwd = '/w/other'
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  on('session.cwd', () => ({ value: cwd }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.list', () => ({ value: [] }) as never)
  on('clock.now', () => ({ value: 1000 }) as never)
  const SKILL = '/u/.claude/plugins/cache/reboot-plugin/reboot/0.4.1/skills/build/SKILL.md'

  // The plugin's own repository, say: no project, so nothing starts.
  await $.tool.call({ tool: 'Read', file_path: SKILL })
  const outside = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect(await outside.findAll({ text: /Reboot/ })).toEqual([])
  await outside.unmount()

  cwd = '/w/app'
  await $.tool.call({ tool: 'Read', file_path: SKILL })
  await $.tool.call({ tool: 'Write', file_path: '/w/app/api/app/v1/app.py', content: '' })
  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await band.findAll({ type: 'Text', text: 'Design \u00b7 ' })).length).toBe(1)
})

test("the band lets a project go once its .rbtrc is gone, and follows the session to another", async ($, on) => {
  let cwd = '/w/a'
  let projects = ['/w/a/.rbtrc', '/w/b/.rbtrc']
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
  on('session.cwd', () => ({ value: cwd }) as never)
  on('fs.exists', ($, e) => ({ value: projects.includes((e as { path: string }).path) }) as never)
  on('fs.list', () => ({ value: [] }) as never)
  on('fs.read', () => ({ value: '' }) as never)
  on('process.run', () => ({ value: { exitCode: 0, stdout: '', stderr: '' } }) as never)
  on('clock.now', () => ({ value: 1000 }) as never)
  const mount = () => $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })

  await $.tool.call({ tool: 'Skill', skill: 'reboot:build' })
  await $.tool.call({ tool: 'Write', file_path: '/w/a/api/app/v1/app.py', content: '' })
  const inA = await mount()
  expect((await inA.findAll({ type: 'Text', text: 'Design \u00b7 ' })).length).toBe(1)
  await inA.unmount()

  // The session moves to another project: A's task is not B's.
  cwd = '/w/b'
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const inB = await mount()
  expect(await inB.findAll({ type: 'Text', text: 'Design \u00b7 ' })).toEqual([])
  expect(await inB.findAll({ type: 'Text', text: 'Prove \u00b7 ' })).toEqual([])
  expect((await inB.findAll({ type: 'Text', text: /^Reboot Status$/ })).length).toBe(1)
  await inB.unmount()

  // B's .rbtrc goes: no project, and the band draws nothing.
  projects = []
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)
  const none = await mount()
  expect(await none.findAll({ text: /Reboot/ })).toEqual([])
})

test('the poll runs on one interval, and stops when the session ends', async ($, on) => {
  const clock = mock.clock(on)
  // The engine beneath: the session starts and ends, the command registers.
  on('command.register', () => ({ value: { command: 'reboot-progress' } }) as never)
  on('session.start', ($, e) => ({ cwd: (e as { cwd: string }).cwd }) as never)
  on('session.end', ($, e) => ({ sessionId: (e as { sessionId: string }).sessionId }) as never)
  let polls = 0
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.read', () => ({ value: '' }) as never)
  on('process.run', ($, e) => {
    if ((e as { argv: string[] }).argv[0] === 'ps') polls++
    return { value: { exitCode: 0, stdout: '', stderr: '' } } as never
  })
  const start = { cwd: '/w/app', surface: 'terminal', isInteractive: true } as never

  await $.session.start(start)
  await clock.advance(2500)
  // A second start (a reload, say) replaces the first interval.
  await $.session.start(start)
  await clock.settle()
  const started = polls
  await clock.advance(3000) // the first interval's time: it no longer polls
  expect(polls).toBe(started)
  await clock.advance(2000) // the second's
  expect(polls).toBe(started + 1)

  await $.session.end({ reason: 'other', sessionId: 's1', resume: {} } as never)
  const ended = polls
  await clock.advance(20_000)
  expect(polls).toBe(ended)
})

test("a store that rejects the build's read once is asked again at the next poll", async ($, on) => {
  const clock = mock.clock(on)
  // The engine beneath: the session starts and ends, the command registers.
  on('command.register', () => ({ value: { command: 'reboot-progress' } }) as never)
  on('session.start', ($, e) => ({ cwd: (e as { cwd: string }).cwd }) as never)
  on('session.end', ($, e) => ({ sessionId: (e as { sessionId: string }).sessionId }) as never)
  let rejected = 0
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  on('fs.read', () => ({ value: '' }) as never)
  on('process.run', () => ({ value: { exitCode: 0, stdout: '', stderr: '' } }) as never)
  on('store.get', ($, e, next) => {
    const key = (e as { key: string }).key
    if (key === 'build:/w/app' && rejected === 0) {
      rejected++
      return next(e) // beneath the test's hooks the bottom one rejects
    }
    return { value: key === 'build:/w/app' ? { kind: 'build', step: 1, isDone: false } : null } as never
  })
  const mount = () => $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })

  await $.session.start({ cwd: '/w/app', surface: 'terminal', isInteractive: true } as never)
  await clock.settle()
  expect(rejected).toBe(1)
  const first = await mount()
  expect(await first.findAll({ type: 'Text', text: 'Design \u00b7 ' })).toEqual([])
  await first.unmount()

  await clock.advance(5000)
  const band = await mount()
  expect((await band.findAll({ type: 'Text', text: 'Design \u00b7 ' })).length).toBe(1)
})

test("a background test run's output over 4 MiB still says how far it is", async ($, on) => {
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)

    return h(Box, {}) as never
  })
  on('clock.now', () => ({ value: 1000 }) as never)
  on('session.cwd', () => ({ value: '/w/app' }) as never)
  on('fs.exists', ($, e) => ({ value: (e as { path: string }).path === '/w/app/.rbtrc' }) as never)
  // The output file is too big to read whole: the read rejects.
  on('fs.read', ($, e, next) => ((e as { path: string }).path === '/tmp/t1.output' ? next(e) : ({ value: '' } as never)))
  on('ui.status', () => ({ value: undefined }) as never)
  on('process.run', ($, e) => {
    const argv = (e as { argv: string[] }).argv
    const stdout =
      argv[0] === 'tail' && argv.at(-1) === '/tmp/t1.output'
        ? 'tests/web_test.py ..........  [ 42%]\n'
        : argv[0] === 'ps'
          ? '  9 /w/app/.venv/bin/python /w/app/.venv/bin/pytest -q'
          : ''
    return { value: { exitCode: 0, stdout, stderr: '' } } as never
  })
  on('tool.call', ($, e) => {
    const isTests = /pytest/.test(String((e as { command?: string }).command))
    return { result: {}, text: isTests ? 'Command running in background with ID: t1\nOutput is being written to: /tmp/t1.output' : 'ok' } as never
  })

  await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q', run_in_background: true } as never)
  // Starting the app polls, which finds the run in ps and reads its output.
  await $.tool.call({ tool: 'Bash', command: 'uv run rbt dev run' })
  await wait(50)

  const band = await $.ui.mount({ plugin: PLUGIN, surface: 'terminal', component: 'AbovePrompt', props: BAND as never })
  expect((await band.findAll({ type: 'Text', text: 'Waiting for the tests to finish: 42% done' })).length).toBe(1)
})
