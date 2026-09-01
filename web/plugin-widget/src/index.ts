export type ValidationState = "passed" | "failed" | "unverified";

export interface ArtifactStatus {
    readonly artifactSha256: string;
    readonly validation: ValidationState;
}

export function summarizeArtifact(status: ArtifactStatus): string {
    if (!/^[0-9a-f]{64}$/.test(status.artifactSha256)) {
        throw new Error("artifactSha256 must be lowercase SHA-256 hex");
    }
    return `${status.validation}:${status.artifactSha256.slice(0, 12)}`;
}
