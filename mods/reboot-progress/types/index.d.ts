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
      /** What is being worked on now, or a Waiting line between turns. */
      activity: string | null
    }
  }
}
