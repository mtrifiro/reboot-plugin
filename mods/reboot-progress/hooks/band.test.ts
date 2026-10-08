import { expect, test } from 'claude-code/testing'

const PLUGIN = 'reboot-progress'

// The test runtime has timers; the hooks module's typings don't declare them.
const wait = (ms: number) =>
  new Promise<void>(resolve =>
    (globalThis as unknown as { setTimeout: (f: () => void, ms: number) => void }).setTimeout(resolve, ms),
  )
const BAND = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 120 }

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the band follows the build on ${surface}`, async ($, on) => {
    // Stand in for the engine beneath: every tool call succeeds.
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    on('fs.exists', () => ({ value: false }) as never)
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
    await $.tool.call({
      tool: 'Write',
      file_path: '/w/app/backend/src/servicers/app.py',
      content: 'def authorizer(self): ...',
    })

    const band = await $.ui.mount({ plugin: PLUGIN, surface, component: 'AbovePrompt', props: BAND as never })
    // A static Status heading: neither the kind of work nor the stage.
    expect((await band.findAll({ type: 'Text', text: /^Status$/ })).length).toBe(1)
    expect(await band.findAll({ type: 'Text', text: /^(Building|Adding Feature|Fixing|Done)$/ })).toEqual([])
    expect(await band.findAll({ type: 'Text', text: /access rules|backend|screens|·/ })).toEqual([])
    // No progress bar: the task's name alone.
    expect(await band.findAll({ type: 'Text', text: /█|░/ })).toEqual([])

    await $.command.run({ command: 'reboot-progress', args: 'hide' } as never)
    expect(await band.findAll({ text: /Reboot/ })).toEqual([])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the activity columns draw on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
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
    expect((await band.findAll({ type: 'Text', text: /^Status$/ })).length).toBe(1)
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a prompt the summary calls a fix shows its Now on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
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
    expect((await band.findAll({ type: 'Text', text: /^Reboot$/ })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: 'Fixing the sign-in button' })).length).toBe(1)
    expect((await band.findAll({ type: 'Text', text: /^Status$/ })).length).toBe(1)
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
    expect((await band.findAll({ type: 'Text', text: 'Opens the dashboard: http://127.0.0.1:9871/' })).length).toBe(1)
    await band.press({ key: 'dashboard' })
    expect(opened).toEqual([['open', 'http://127.0.0.1:9871/']])
  })
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`Now leaves "Idle" the moment a prompt is sent on ${surface}`, async ($, on) => {
    on('fs.exists', () => ({ value: false }) as never)
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

test('the Reboot logo draws beside Reboot where the surface has Svg', async ($, on) => {
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
  // Where the logo can't draw, the word carries its color.
  const [word] = await terminal.findAll({ type: 'Text', text: /^Reboot$/ })
  expect((word as { props: { color?: string } }).props.color).toBe('success')
  const [heading] = await terminal.findAll({ type: 'Text', text: /^Status$/ })
  expect((heading as { props: { color?: string } }).props.color).toBe('success')
  const [plain] = await desktop.findAll({ type: 'Text', text: /^Reboot$/ })
  expect((plain as { props: { color?: string } }).props.color).toBe(undefined)
})

for (const surface of ['terminal', 'desktop'] as const) {
  test(`a deploy's output toasts and adds a Cloud button on ${surface}`, async ($, on) => {
    const toasts: string[] = []
    const opened: string[][] = []
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
