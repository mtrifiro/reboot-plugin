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
      /** Whether a test run is going, so the band waits on it rather than saying Idle. */
      isTesting: boolean
      /** The latest deploy. */
      deploy: Deploy | null
      /** The clock at the latest poll, so a running deploy's time redraws. */
      clock: number
    }
  }
}
