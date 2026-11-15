---
title: Getting Started
---
# Getting Started

Learn how to write documents and build your static website.

## Directory Structure

```text
minssg/
├── content/           # Place your .md markdown files here
│   ├── index.md
│   └── getting-started.md
├── template.html      # Responsive HTML layout
└── minssg.py          # Generator script
```

## Building the Site

To compile all pages into `dist/`:

```powershell
python minssg.py build
```

To run the local server with hot preview:

```powershell
python minssg.py serve
```
