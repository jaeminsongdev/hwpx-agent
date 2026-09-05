export interface HostExtensionCapabilities {
    readonly available: boolean;
    readonly canRequestDisplayMode: boolean;
    readonly canOpenExternal: boolean;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function detectOptionalHostExtensions(
    scope: unknown,
): HostExtensionCapabilities {
    if (!isRecord(scope)) {
        return {
            available: false,
            canRequestDisplayMode: false,
            canOpenExternal: false,
        };
    }
    const candidate = scope.openai;
    if (!isRecord(candidate)) {
        return {
            available: false,
            canRequestDisplayMode: false,
            canOpenExternal: false,
        };
    }
    return {
        available: true,
        canRequestDisplayMode:
            typeof candidate.requestDisplayMode === "function",
        canOpenExternal: typeof candidate.openExternal === "function",
    };
}
