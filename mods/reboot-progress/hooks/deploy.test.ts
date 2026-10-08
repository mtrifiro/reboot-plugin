import { describe, expect, test } from 'claude-code/testing'

import { advanceDeploy, afterOutput, beginDeploy, deployLine, elapsed, FAILED_MS, isRunning, isShown, outcomeOf, seenIn, STARTING_MS } from './deploy'

const PS_UP = '/usr/bin/python3 /w/app/.venv/bin/rbt cloud up --organization=acme --name=app'
const PS_BUILD = `${PS_UP}\ndocker build --file=Dockerfile --tag=reg/app:1 .`
const PS_PUSH = `${PS_UP}\ndocker --config /tmp/x push reg/app:1`
const PS_WRANGLER = 'node /n/.bin/wrangler pages deploy web/dist --project-name=app --branch=main'
const OUT_UP = `[😇] checking permissions... ✅
[🚀] deploying... ✅

  'app' revision 7 is available:

  Your API is available at:      https://a1b2c3.c1.rbt.cloud:9991
  MCP clients can connect at:    https://a1b2c3.c1.rbt.cloud:9991/mcp
`
const OUT_FAILED = `[🚀] deploying... Could not deploy revision 8:
  Application failed health checks

### Logs for revision 8 ###`

describe('what the process list shows of a deploy', () => {
  test('rbt cloud up, docker build and push, wrangler', () => {
    expect(seenIn(PS_UP)).toEqual({ isUp: true, isBuild: false, isPush: false, isPublish: false })
    expect(seenIn(PS_BUILD).isBuild).toBe(true)
    expect(seenIn(PS_PUSH).isPush).toBe(true)
    expect(seenIn(PS_WRANGLER).isPublish).toBe(true)
    expect(seenIn('rbt dev run\nrbt cloud logs --follow')).toEqual({
      isUp: false,
      isBuild: false,
      isPush: false,
      isPublish: false,
    })
  })
})

describe('how a deploy moves', () => {
  test('through the stages of rbt cloud up', () => {
    let d = advanceDeploy(null, seenIn(PS_UP), 0)
    expect(d?.stage).toBe('checking')
    d = advanceDeploy(d, seenIn(PS_BUILD), 5000)
    expect(d?.stage).toBe('build')
    d = advanceDeploy(d, seenIn(PS_PUSH), 60000)
    expect(d?.stage).toBe('push')
    // Docker done, up still waiting on the revision.
    d = advanceDeploy(d, seenIn(PS_UP), 90000)
    expect(d?.stage).toBe('rollout')
    expect(d?.startedAt).toBe(0)
  })

  test('its output says it is starting, then the app answering makes it live', () => {
    const running = advanceDeploy(null, seenIn(PS_PUSH), 0)
    const { deploy, toast } = afterOutput(running, outcomeOf(OUT_UP), 100000)
    expect(toast).toBe('Deployed revision 7 to Reboot Cloud')
    expect(deploy?.stage).toBe('starting')
    expect(deploy?.apiUrl).toBe('https://a1b2c3.c1.rbt.cloud:9991')
    expect(advanceDeploy(deploy, seenIn(''), 105000)?.stage).toBe('starting')
    expect(advanceDeploy(deploy, seenIn(''), 110000, true)?.stage).toBe('live')
    // A revision that never answers stops holding the band.
    expect(advanceDeploy(deploy, seenIn(''), 100000 + STARTING_MS + 1)?.stage).toBe('deployed')
  })

  test('a failure is toasted with its reason', () => {
    const running = advanceDeploy(null, seenIn(PS_UP), 0)
    const { deploy, toast } = afterOutput(running, outcomeOf(OUT_FAILED), 1000)
    expect(toast).toBe('Deploy failed: Application failed health checks')
    expect(deploy?.stage).toBe('failed')
    expect(isRunning(deploy)).toBe(false)
    // Shown a while, its time stopped where it failed, then gone.
    expect(isShown(deploy, 1000 + FAILED_MS - 1)).toBe(true)
    expect(deployLine(deploy!, 60000)).toBe('Deploy failed: Application failed health checks · 1s')
    expect(isShown(deploy, 1000 + FAILED_MS)).toBe(false)
  })

  test('up exiting before its output is read: starting with a known URL, else deployed', () => {
    const known = { ...beginDeploy('rollout', 0, null), apiUrl: 'https://x.rbt.cloud:9991' }
    expect(advanceDeploy(known, seenIn(''), 1000)?.stage).toBe('starting')
    expect(advanceDeploy(beginDeploy('rollout', 0, null), seenIn(''), 1000)?.stage).toBe('deployed')
  })

  test('publishing the frontend, and the site it lands on', () => {
    const d = advanceDeploy(null, seenIn(PS_WRANGLER), 0)
    expect(d?.stage).toBe('publish')
    const { deploy, toast } = afterOutput(d, outcomeOf('✨ Deployment complete! Take a peek over at https://abc.app.pages.dev'), 9000)
    expect(toast).toBe('Frontend published')
    expect(deploy?.siteUrl).toBe('https://abc.app.pages.dev/')
    expect(advanceDeploy(d, seenIn(''), 9000)?.stage).toBe('published')
  })

  test('a new deploy keeps the URLs of the last', () => {
    const done = { ...beginDeploy('live', 0, null), apiUrl: 'https://x.rbt.cloud:9991', siteUrl: 'https://s.pages.dev/' }
    const next = advanceDeploy(done, seenIn(PS_UP), 5000)
    expect(next?.stage).toBe('checking')
    expect(next?.startedAt).toBe(5000)
    expect(next?.apiUrl).toBe('https://x.rbt.cloud:9991')
  })

  test('output with nothing of a deploy changes nothing', () => {
    expect(afterOutput(null, outcomeOf('3 passed in 1.2s'), 0)).toEqual({ deploy: null, toast: null })
  })
})

describe('the band line', () => {
  test('names the stage and the time so far', () => {
    expect(elapsed(45000)).toBe('45s')
    expect(elapsed(72000)).toBe('1m 12s')
    expect(deployLine(beginDeploy('push', 0, null), 72000)).toBe(
      'Deploying to Reboot Cloud: pushing the image · 1m 12s',
    )
    expect(deployLine({ ...beginDeploy('starting', 0, null), revision: 7 }, 5000)).toBe(
      'Deploying to Reboot Cloud: revision 7 is starting up · 5s',
    )
  })
})
