import {
    App,
    applyDocumentTheme,
    applyHostStyleVariables,
} from "@modelcontextprotocol/ext-apps";

import type {
    HostContextInput,
    ProjectOpenCall,
    ToolResultInput,
    WidgetPort,
} from "./bridge.js";

export class McpAppPort implements WidgetPort {
    private readonly app = new App(
        { name: "HWPX Agent", version: "1.0.0" },
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

    onToolResult(handler: (value: ToolResultInput) => void): () => void {
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
        handler: (value: HostContextInput) => void,
    ): () => void {
        const callback = (
            params: Parameters<
                NonNullable<typeof this.app.onhostcontextchanged>
            >[0],
        ) => {
            this.applyHostPresentation(params);
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

    getHostContext(): HostContextInput | undefined {
        const context = this.app.getHostContext();
        this.applyHostPresentation(context);
        return context;
    }

    async callServerTool(call: ProjectOpenCall): Promise<unknown> {
        return this.app.callServerTool(call);
    }

    async close(): Promise<void> {
        await this.app.close();
    }

    private applyHostPresentation(
        context: ReturnType<App["getHostContext"]>,
    ): void {
        if (context?.theme === "light" || context?.theme === "dark") {
            applyDocumentTheme(context.theme);
        }
        if (context?.styles?.variables !== undefined) {
            applyHostStyleVariables(context.styles.variables);
        }
    }
}
