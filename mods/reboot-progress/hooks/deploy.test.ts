import { describe, expect, test } from 'claude-code/testing'

import { advanceDeploy, afterOutput, beginDeploy, deployLine, elapsed, FAILED_MS, deployProgram, isDeployCommand, isRunning, isShown, outcomeOf, SCRIPT_MS, seenIn, STARTING_MS } from './deploy'

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

describe('which commands are deploys', () => {
  test('rbt cloud up, wrangler pages deploy and a project deploy script are', () => {
    expect(isDeployCommand('uv run rbt cloud up --application-name=app --organization=acme')).toBe(true)
    expect(isDeployCommand('npx --yes wrangler@4 pages deploy web/dist --project-name=app --branch=main')).toBe(true)
    expect(isDeployCommand('scripts/deploy.sh --frontend-only')).toBe(true)
    expect(isDeployCommand('cd app && ./scripts/deploy.sh')).toBe(true)
    expect(isDeployCommand('set -a; . ./.deploy.env; set +a; uv run rbt cloud up --organization="$ORG"')).toBe(true)
    expect(isDeployCommand('( cd "$build/web" && npx --yes wrangler@4 pages deploy dist )')).toBe(true)
  })

  test('a command that only prints a deploy guide or a ledger is not', () => {
    // Printing reboot-crm's deploy guide put its pages.dev site on the
    // band of a session that deployed nothing (2026-10-08).
    expect(isDeployCommand("awk '/^## 7/,/^## 8/' docs/DEPLOYING.md")).toBe(false)
    expect(isDeployCommand('grep -n pages.dev deploy/ledger.jsonl')).toBe(false)
    expect(isDeployCommand('cat scripts/deploy.sh')).toBe(false)
    expect(isDeployCommand('grep -n "rbt cloud up" docs/DEPLOYING.md')).toBe(false)
    expect(isDeployCommand('ls scripts/deploy.sh.bak && echo wrangler pages deploy')).toBe(false)
  })
})

describe('a deploy script', () => {
  test("stays checking while its own steps run, before rbt cloud up shows", () => {
    const d = beginDeploy('checking', 0, null, 'script')
    const none = { isUp: false, isBuild: false, isPush: false, isPublish: false }
    expect(advanceDeploy(d, none, 60_000)).toBe(d)
    expect(advanceDeploy(d, none, SCRIPT_MS + 1)?.stage).toBe('deployed')
    expect(advanceDeploy(d, { ...none, isUp: true, isBuild: true }, 60_000)?.stage).toBe('build')
  })

  test('names the site it serves', () => {
    expect(outcomeOf('deploy: https://app.example.com serves 9f8e7d (2026-10-09)').siteUrl).toBe('https://app.example.com/')
  })
})

describe('which deploy a command starts', () => {
  test('rbt cloud up and a deploy script start one; wrangler publishes', () => {
    expect(deployProgram('uv run rbt cloud up --organization=acme')).toBe('up')
    expect(deployProgram('scripts/deploy.sh')).toBe('script')
    expect(deployProgram('npx wrangler pages deploy dist --project-name=app')).toBe('publish')
  })

  test('wrappers, runners and a path to the program are seen through', () => {
    expect(deployProgram('timeout 900 uv run rbt cloud up --organization=acme')).toBe('up')
    expect(deployProgram('uv run --directory app rbt cloud up')).toBe('up')
    expect(deployProgram('uv run --no-sync rbt cloud up')).toBe('up')
    expect(deployProgram('.venv/bin/rbt cloud up')).toBe('up')
    expect(deployProgram('nohup uv run rbt cloud up > up.log')).toBe('up')
    expect(deployProgram('npx -y wrangler pages deploy dist')).toBe('publish')
    expect(deployProgram('bunx wrangler@4 pages deploy dist')).toBe('publish')
    expect(deployProgram("bash -lc 'scripts/deploy.sh'")).toBe('script')
  })

  test('a dry run and a heredoc holding the words start nothing', () => {
    expect(deployProgram('scripts/deploy.sh --dry-run')).toBe(null)
    expect(deployProgram("cat > note.md <<'EOF'\nrbt cloud up\nEOF\ncat note.md")).toBe(null)
    expect(deployProgram('git commit -m "rbt cloud up"')).toBe(null)
  })

  test('a command whose text only contains the words starts nothing', () => {
    // A heredoc writing this very test once put "Deploying to Reboot
    // Cloud" on the band of a session that deployed nothing (2026-10-08).
    expect(deployProgram("python3 - <<'EOF'\nexpect(isDeployCommand('uv run rbt cloud up'))\nEOF")).toBe(null)
    expect(deployProgram('grep -rn "rbt cloud up" skills/')).toBe(null)
  })
})
