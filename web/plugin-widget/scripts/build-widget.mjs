import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "esbuild";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = resolve(packageRoot, "dist");

function inlineHtml(title, javascript, css) {
    const safeJavascript = javascript.replaceAll("</script", "<\\/script");
    return `<!doctype html>\n<html lang="ko-KR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="color-scheme" content="light dark">\n<title>${title}</title>\n<style>${css}</style>\n</head>\n<body>\n<div id="root"></div>\n<script>${safeJavascript}</script>\n</body>\n</html>\n`;
}

async function bundle(entry, extraCss, outputName, title) {
    const result = await build({
        absWorkingDir: packageRoot,
        bundle: true,
        charset: "utf8",
        entryPoints: [entry],
        format: "iife",
        legalComments: "none",
        minify: true,
        outfile: "widget.js",
        platform: "browser",
        sourcemap: false,
        target: ["es2022"],
        treeShaking: true,
        write: false,
    });
    const javascript = result.outputFiles.find((file) =>
        file.path.endsWith("widget.js"),
    );
    const bundledCss = result.outputFiles.find((file) =>
        file.path.endsWith("widget.css"),
    );
    if (javascript === undefined)
        throw new Error("esbuild did not produce JavaScript");
    const cssParts = [bundledCss?.text ?? ""];
    if (extraCss !== null)
        cssParts.push(await readFile(resolve(packageRoot, extraCss), "utf8"));
    const html = inlineHtml(title, javascript.text, cssParts.join("\n"));
    await writeFile(resolve(outputDirectory, outputName), html, {
        encoding: "utf8",
    });
}

await mkdir(outputDirectory, { recursive: true });
await bundle("src/component.tsx", null, "widget-v1.html", "HWPX Agent");
await bundle(
    "src/preview.tsx",
    "src/preview.css",
    "preview.html",
    "HWPX Agent preview",
);
