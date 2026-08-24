import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

export type PythonInvocation = {
    command: string;
    prefixArgs: string[];
    source: "configured" | "environment" | "installed" | "system";
};

type RuntimeEnvironment = Record<string, string | undefined>;

export function resolvePythonInvocation(
    configuredCommand: string | undefined,
    platform: NodeJS.Platform = process.platform,
    environment: RuntimeEnvironment = process.env,
    pathExists: (candidate: string) => boolean = fs.existsSync,
): PythonInvocation {
    const configured = configuredCommand?.trim();
    if (configured) {
        return { command: configured, prefixArgs: [], source: "configured" };
    }

    const environmentCommand = environment.PREFIX_PYTHON_ENGINE?.trim();
    if (environmentCommand) {
        return { command: environmentCommand, prefixArgs: [], source: "environment" };
    }

    for (const candidate of installedRuntimeCandidates(platform, environment)) {
        if (pathExists(candidate)) {
            return { command: candidate, prefixArgs: [], source: "installed" };
        }
    }

    if (platform === "win32") {
        return { command: "py", prefixArgs: ["-3.12"], source: "system" };
    }
    return { command: "python3.12", prefixArgs: [], source: "system" };
}

export function installedRuntimeCandidates(
    platform: NodeJS.Platform = process.platform,
    environment: RuntimeEnvironment = process.env,
): string[] {
    if (platform === "win32") {
        const localAppData = environment.LOCALAPPDATA?.trim();
        if (!localAppData) {
            return [];
        }
        return [path.win32.join(localAppData, "FastIndustries", "PREFIX for Python", "runtime", "python.exe")];
    }

    const dataRoot = environment.XDG_DATA_HOME?.trim()
        || (environment.HOME?.trim() ? path.posix.join(environment.HOME.trim(), ".local", "share") : path.posix.join(os.homedir(), ".local", "share"));
    return [path.posix.join(dataRoot, "fastindustries", "prefix-python", "runtime", "prefix-python-python")];
}

export function formatInvocation(invocation: PythonInvocation): string {
    return [invocation.command, ...invocation.prefixArgs].join(" ");
}
