/** Whether the model has read api-schema-evolution.md this session. */
export type HasReadRules = boolean

declare module 'claude-code' {
  interface PluginState {
    'reboot-schema-guard': {
      hasReadRules: HasReadRules
    }
  }
}
