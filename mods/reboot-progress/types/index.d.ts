/** The band's first row: the last finished task and the current one. */
export type Activity = { justCompleted: string | null; now: string }

export type Build = {
  /** Index into STEPS of the furthest step reached. */
  step: number
  /** True once the build reached Run; the band clears at the next prompt. */
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
      /** What just finished and what is being worked on now. */
      activity: Activity | null
    }
  }
}
