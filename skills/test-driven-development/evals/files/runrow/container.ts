type Factory = (resolve: (name: string) => unknown) => unknown;

export interface Config {
  registrations: Record<string, Factory>;
  handlers: string[];
}

/**
 * Wire the app. Resolves every handler eagerly so a missing registration
 * fails at startup instead of on the first request.
 */
export function buildContainer(config: Config): Map<string, unknown> {
  const built = new Map<string, unknown>();
  const resolve = (name: string): unknown => {
    if (built.has(name)) return built.get(name);
    const factory = config.registrations[name];
    if (!factory) throw new Error(`No registration for '${name}'`);
    const instance = factory(resolve);
    built.set(name, instance);
    return instance;
  };
  for (const handler of config.handlers) resolve(handler);
  return built;
}
