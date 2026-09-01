---
name: configure-page-layout
description: Set or change Hancom paper size, custom dimensions, orientation, margins, binding/gutter, sections, columns, headers, footers, master pages, and page numbering.
---

# Configure Page Layout

## Use this when

The user mentions A3/A4/B4, custom paper dimensions, portrait/landscape, margins, two columns, section-specific layout, headers/footers, or page numbers.

## Workflow

1. Convert the request into exact `page.*` operations and section selectors.
2. For colloquial or region-dependent names, present candidate presets with exact width×height mm and do not choose silently.
3. Check printable body width/height, column width+gaps, header/footer distance, gutter, and anchored-object/table overflow.
4. Dry-run and show exact dimensions and affected sections/pages.
5. Execute, semantic reopen, render, and compare page count/major bounds with the requested oracle level.

## Required error behavior

Invalid or physically impossible dimensions fail with a layout error. Do not silently shrink content or alter margins unless the user requested an auto-fit policy.
