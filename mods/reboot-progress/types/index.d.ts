export type Build = {
  /** Index into STEPS of the furthest step reached. */
  step: number
  /** True once the build reached Run; the band clears at the next prompt. */
  isDone: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'reboot-progress': {
      build: Build | null
      isHidden: boolean
      root: string | null
    }
  }
}
