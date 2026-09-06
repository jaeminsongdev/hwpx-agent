import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "esbuild";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = resolve(packageRoot, "dist");

function inlineHtml(title, javascript, css) {
    const safeJavascript = javascript.replaceAll("</script", "<\\/script");
    return `<!doctype html>\n<html lang="ko-KR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="color-scheme" content="light dark">\n<title>${title}</title>\n<style>${css}</style>\n</head>\n<body>\n<div id="root"></div>\n<script>${safeJavascript}</script>\n</body>\n</html>\n`;
}

async function bundle(entry, outputName, title) {
    const result = await build({
        absWorkingDir: packageRoot,
        bundle: true,
        charset: "utf8",
        entryPoints: [entry],
        format: "iife",
        legalComments: "none",
        minify: true,
        outfile: "continuity.js",
        platform: "browser",
        sourcemap: false,
        target: ["es2022"],
        treeShaking: true,
        write: false,
    });
    const javascript = result.outputFiles.find((file) =>
        file.path.endsWith("continuity.js"),
    );
    const css = result.outputFiles.find((file) =>
        file.path.endsWith("continuity.css"),
    );
    if (javascript === undefined)
        throw new Error("missing continuity JavaScript");
    const html = inlineHtml(title, javascript.text, css?.text ?? "");
    await writeFile(resolve(outputDirectory, outputName), html, "utf8");
}

async function hostHarness(entry, outputName, title, height) {
    const result = await build({
        absWorkingDir: packageRoot,
        bundle: true,
        charset: "utf8",
        entryPoints: [entry],
        format: "iife",
        legalComments: "none",
        minify: true,
        outfile: "continuity-host.js",
        platform: "browser",
        sourcemap: false,
        target: ["es2022"],
        treeShaking: true,
        write: false,
    });
    const javascript = result.outputFiles.find((file) =>
        file.path.endsWith("continuity-host.js"),
    );
    if (javascript === undefined)
        throw new Error("missing E2E host JavaScript");
    const html = `<!doctype html>\n<html lang="ko-KR">\n<head>\n<meta charset="utf-8">\n<title>${title}</title>\n<style>body{font-family:system-ui;margin:16px}iframe{width:900px;height:${height}px;border:0}#e2e-result{font:14px monospace}#e2e-result[data-state="pass"]{color:#117a4b}#e2e-result[data-state="fail"]{color:#b42318}</style>\n</head>\n<body>\n<p id="e2e-result" data-state="running">RUNNING</p>\n<iframe id="continuity-frame"></iframe>\n<script>${javascript.text.replaceAll("</script", "<\\/script")}</script>\n</body>\n</html>\n`;
    await writeFile(resolve(outputDirectory, outputName), html, "utf8");
}

await mkdir(outputDirectory, { recursive: true });
await bundle(
    "src/continuity-component.tsx",
    "continuity-widget-v1.html",
    "HWPX Agent project continuity",
);
await bundle(
    "src/continuity-component.tsx",
    "continuity-widget-v2.html",
    "HWPX Agent stale-head resolution",
);
await bundle(
    "src/continuity-preview.tsx",
    "continuity-preview.html",
    "HWPX Agent continuity preview",
);
await hostHarness(
    "src/continuity-e2e-host.ts",
    "continuity-e2e-host.html",
    "HWPX Agent continuity E2E",
    620,
);
await hostHarness(
    "src/continuity-v2-e2e-host.ts",
    "continuity-v2-e2e-host.html",
    "HWPX Agent continuity v2 E2E",
    760,
);
