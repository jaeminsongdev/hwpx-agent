import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = resolve(packageRoot, "dist");
function inlineHtml(title, javascript, css) {
    return `<!doctype html>\n<html lang="ko-KR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="color-scheme" content="light dark">\n<title>${title}</title>\n<style>${css}</style>\n</head>\n<body>\n<div id="root"></div>\n<script>${javascript.replaceAll("</script", "<\\/script")}</script>\n</body>\n</html>\n`;
}
async function bundle(entry, outputName, title) {
    const built = await build({
        absWorkingDir: packageRoot,
        bundle: true,
        charset: "utf8",
        entryPoints: [entry],
        format: "iife",
        legalComments: "none",
        minify: true,
        outfile: "plan-review.js",
        platform: "browser",
        sourcemap: false,
        target: ["es2022"],
        treeShaking: true,
        write: false,
    });
    const js = built.outputFiles.find((file) =>
        file.path.endsWith("plan-review.js"),
    );
    const css = built.outputFiles.find((file) =>
        file.path.endsWith("plan-review.css"),
    );
    if (js === undefined) throw new Error("missing plan review JavaScript");
    await writeFile(
        resolve(outputDirectory, outputName),
        inlineHtml(title, js.text, css?.text ?? ""),
        "utf8",
    );
}
async function harness() {
    const built = await build({
        absWorkingDir: packageRoot,
        bundle: true,
        charset: "utf8",
        entryPoints: ["src/plan-review-e2e-host.ts"],
        format: "iife",
        legalComments: "none",
        minify: true,
        outfile: "plan-review-host.js",
        platform: "browser",
        sourcemap: false,
        target: ["es2022"],
        treeShaking: true,
        write: false,
    });
    const js = built.outputFiles.find((file) =>
        file.path.endsWith("plan-review-host.js"),
    );
    if (js === undefined)
        throw new Error("missing plan review E2E host JavaScript");
    const html = `<!doctype html>\n<html lang="ko-KR">\n<head>\n<meta charset="utf-8">\n<title>HWPX Agent plan review E2E</title>\n<style>body{font-family:system-ui;margin:16px}iframe{width:940px;height:760px;border:0}#e2e-result{font:14px monospace}#e2e-result[data-state="pass"]{color:#117a4b}#e2e-result[data-state="fail"]{color:#b42318}</style>\n</head>\n<body>\n<p id="e2e-result" data-state="running">RUNNING</p>\n<iframe id="plan-review-frame"></iframe>\n<script>${js.text.replaceAll("</script", "<\\/script")}</script>\n</body>\n</html>\n`;
    await writeFile(
        resolve(outputDirectory, "plan-review-e2e-host.html"),
        html,
        "utf8",
    );
}
await mkdir(outputDirectory, { recursive: true });
await bundle(
    "src/plan-review-component.tsx",
    "plan-review-widget-v1.html",
    "HWPX Agent plan review",
);
await bundle(
    "src/plan-review-preview.tsx",
    "plan-review-preview.html",
    "HWPX Agent plan review preview",
);
await harness();
