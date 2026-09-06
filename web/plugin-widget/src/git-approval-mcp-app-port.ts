import {
    App,
    applyDocumentTheme,
    applyHostStyleVariables,
} from "@modelcontextprotocol/ext-apps";
import type {
    GitApprovalPort,
    GitApprovalServerCall,
    GitApprovalToolResultNotification,
} from "./git-approval-controller.js";

export class GitApprovalMcpAppPort implements GitApprovalPort {
    private readonly app = new App(
        { name: "HWPX Agent Git approval", version: "1.0.0" },
        { availableDisplayModes: ["inline"] },
        { autoResize: true, strict: true, allowUnsafeEval: false },
    );
    onToolInput(handler: (value: unknown) => void): () => void {
        const callback = (
            params: Parameters<NonNullable<typeof this.app.ontoolinput>>[0],
        ) => handler(params.arguments);
        this.app.addEventListener("toolinput", callback);
        return () => this.app.removeEventListener("toolinput", callback);
    }
    onToolResult(
        handler: (value: GitApprovalToolResultNotification) => void,
    ): () => void {
        const callback = (
            params: Parameters<NonNullable<typeof this.app.ontoolresult>>[0],
        ) => handler(params);
        this.app.addEventListener("toolresult", callback);
        return () => this.app.removeEventListener("toolresult", callback);
    }
    onToolCancelled(handler: () => void): () => void {
        const callback = () => handler();
        this.app.addEventListener("toolcancelled", callback);
        return () => this.app.removeEventListener("toolcancelled", callback);
    }
    onHostContextChanged(
        handler: (value: { readonly theme?: unknown }) => void,
    ): () => void {
        const callback = (
            params: Parameters<
                NonNullable<typeof this.app.onhostcontextchanged>
            >[0],
        ) => {
            this.apply(params);
            handler(params);
        };
        this.app.addEventListener("hostcontextchanged", callback);
        return () =>
            this.app.removeEventListener("hostcontextchanged", callback);
    }
    onTeardown(handler: () => void): () => void {
        const callback = () => {
            handler();
            return {};
        };
        this.app.onteardown = callback;
        return () => {
            if (this.app.onteardown === callback)
                this.app.onteardown = undefined;
        };
    }
    async connect(): Promise<void> {
        await this.app.connect();
    }
    getHostContext(): { readonly theme?: unknown } | undefined {
        const value = this.app.getHostContext();
        this.apply(value);
        return value;
    }
    async callServerTool(call: GitApprovalServerCall): Promise<unknown> {
        return this.app.callServerTool(call);
    }
    async close(): Promise<void> {
        await this.app.close();
    }
    private apply(context: ReturnType<App["getHostContext"]>): void {
        if (context?.theme === "light" || context?.theme === "dark")
            applyDocumentTheme(context.theme);
        if (context?.styles?.variables !== undefined)
            applyHostStyleVariables(context.styles.variables);
    }
}
