/** The band's first row: the last finished task and the current one. */
export type Activity = { justCompleted: string | null; now: string }

/** The task the bar follows: a new app, a feature, or a bug fix. */
export type Build = {
  kind: 'build' | 'feature' | 'fix'
  /** Index into STEPS of the furthest step reached. */
  step: number
  /** True once the task reached its last step; the band clears at the next prompt. */
  isDone: boolean
  /** True when restored from an earlier session and not yet moved in this one. */
  isRestored?: boolean
}

/** Where a deploy is: `rbt cloud up`'s stages, the revision starting, the frontend's publish, and how each ended. */
export type DeployStage =
  | 'checking'
  | 'build'
  | 'push'
  | 'rollout'
  | 'starting'
  | 'publish'
  | 'live'
  | 'deployed'
  | 'published'
  | 'failed'

/** The latest deploy, and the deployed URLs the band's buttons open. */
export type Deploy = {
  stage: DeployStage
  /** What started it: `rbt cloud up` itself, a project's `scripts/deploy.sh`, or `wrangler`; absent on a deploy stored before this was kept. */
  source?: 'up' | 'script' | 'publish'
  /** When the deploy started, for the time the band shows. */
  startedAt: number
  /** When it reached its stage, for how long a revision may take to start. */
  stageAt: number
  revision: number | null
  /** The Reboot Cloud app's URL (`https://<id>.<cell>.rbt.cloud:9991`). */
  apiUrl: string | null
  /** The published frontend's URL. */
  siteUrl: string | null
  failure: string | null
}

/** A test run while it goes: when it was first seen, where its output is written, and how far it is. */
export type TestRun = {
  /** The run's command from the test runner on (`pytest tests -q -k transfer`), which keys its last time. */
  command: string
  startedAt: number
  /** When a poll last saw it, so its time is known once it ends. */
  seenAt: number
  /** How long the same command took last time in this project; null on a first run. */
  expectedMs: number | null
  /** A background run's output file (from its Bash result); null for a run in the foreground. */
  outputPath: string | null
  /** How far it is, from its output's `[ 42%]` or `[12/40]`; null when the output doesn't say. */
  percent: number | null
  /** How many tests failed so far. */
  failed: number
}

/** One test module in a run's `.reboot/test-run.json`. */
export type SuiteModule = {
  name: string
  /** `rerun` is a harness failure (a hang, a server not ready), not the app failing. */
  status: 'pending' | 'running' | 'passed' | 'failed' | 'rerun'
  passed: number | null
  failed: number | null
  skipped: number | null
  seconds: number | null
  /** When it started running, if the runner says. */
  startedAt: number | null
}

/** A test run as its runner records it in `.reboot/test-run.json`. */
export type SuiteRun = { startedAt: number; finishedAt: number | null; modules: SuiteModule[] }

/** The run the band shows, and when it should end (null without the history to say). */
export type SuiteView = { run: SuiteRun; expectedAt: number | null }

declare module 'claude-code' {
  interface PluginState {
    'reboot-progress': {
      build: Build | null
      isHidden: boolean
      root: string | null
      /** The dashboard and front-end links, while each serves. */
      links: { dashboard: string | null; app: string | null }
      /** What just finished and what is being worked on now. */
      activity: Activity | null
      /** Whether a turn is running: session state, so a reload mid-turn keeps it. */
      isTurnActive: boolean
      /** Whether the project serves MCP (`frontend/mcp`), so its Reboot Cloud URL is an MCP server. */
      isMcp: boolean
      /** The test run going, so the band shows how far it is rather than Idle; null when none. */
      testRun: TestRun | null
      /** The run `.reboot/test-run.json` records, while it goes and after, until code changes; null when none. */
      suite: SuiteView | null
      /** When a Write or Edit last changed code, so a finished run's result goes once it is out of date. */
      lastEditAt: number
      /** Whether the turn waits on a test run in the foreground (a Bash call running it). */
      isAwaitingTests: boolean
      /** The latest deploy. */
      deploy: Deploy | null
      /** The deployed links the buttons open: only ones that answered a check (`checkLinks`). */
      deployedLinks: { cloud: string | null; site: string | null }
      /** The clock at the latest poll, so a running deploy's time redraws. */
      clock: number
    }
  }
}
