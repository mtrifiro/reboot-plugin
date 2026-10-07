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
    }
  }
}
