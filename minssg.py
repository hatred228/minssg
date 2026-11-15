#!/usr/bin/env python3
# path: minssg/minssg.py
# context: Python 3.15 / minssg / static site generator
import sys
import os
import re
import html
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

def parse_markdown(md_text: str) -> tuple[dict, str]:
    """Parses frontmatter and converts standard markdown to HTML."""
    meta = {}
    content = md_text

    # Frontmatter extraction: --- title: ... ---
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
            content = parts[2]

    # Pre-process code blocks: ```lang ... ```
    code_blocks = []
    def save_code_block(match):
        code_content = html.escape(match.group(2).strip())
        code_blocks.append(f"<pre><code>{code_content}</code></pre>")
        return f"<!--CODE_BLOCK_{len(code_blocks)-1}-->"

    content = re.sub(r"```(\w*)\n([\s\S]*?)```", save_code_block, content)

    # Inline replacements
    lines = content.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Unordered list: - or *
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = stripped[2:]
            # inline code
            item = re.sub(r"`([^`]+)`", r"<code>\1</code>", item)
            # bold & italic
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", item)
            html_lines.append(f"<li>{item}</li>")
            continue
        elif in_list:
            html_lines.append("</ul>")
            in_list = False

        if not stripped:
            continue

        # Code block placeholder
        if stripped.startswith("<!--CODE_BLOCK_"):
            html_lines.append(stripped)
            continue

        # Headings: #, ##, ###
        if stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            if "title" not in meta:
                meta["title"] = stripped[2:]
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("> "):
            html_lines.append(f"<blockquote><p>{stripped[2:]}</p></blockquote>")
        else:
            # Paragraph with inline elements
            p = stripped
            p = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', p)
            p = re.sub(r"`([^`]+)`", r"<code>\1</code>", p)
            p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", p)
            html_lines.append(f"<p>{p}</p>")

    if in_list:
        html_lines.append("</ul>")

    out_html = "\n".join(html_lines)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        out_html = out_html.replace(f"<!--CODE_BLOCK_{i}-->", block)

    if "title" not in meta:
        meta["title"] = "Documentation"

    return meta, out_html

def build_site(content_dir: str = "content", output_dir: str = "dist", template_path: str = "template.html"):
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(template_path):
        print(f"[-] Template not found at {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Discover all .md files
    md_files = [f for f in os.listdir(content_dir) if f.endswith(".md")]
    md_files.sort(key=lambda x: (x != "index.md", x))

    pages = []
    for f in md_files:
        src_path = os.path.join(content_dir, f)
        with open(src_path, "r", encoding="utf-8") as file:
            meta, body = parse_markdown(file.read())
        slug = f[:-3] + ".html"
        pages.append({
            "filename": f,
            "slug": slug,
            "title": meta.get("title", f[:-3].title()),
            "body": body
        })

    # Render each page
    for page in pages:
        # Build sidebar links
        nav_items = []
        for p in pages:
            active = ' class="active"' if p["slug"] == page["slug"] else ''
            nav_items.append(f'<li><a href="{p["slug"]}"{active}>{p["title"]}</a></li>')
        nav_html = "\n".join(nav_items)

        rendered = template.replace("{{ title }}", page["title"])
        rendered = rendered.replace("{{ nav_links }}", nav_html)
        rendered = rendered.replace("{{ content }}", page["body"])

        out_path = os.path.join(output_dir, page["slug"])
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(rendered)

    print(f"[+] Successfully built {len(pages)} pages into '{output_dir}/'")

def serve_site(directory: str = "dist", port: int = 8000):
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
        def log_message(self, format, *args):
            return

    server = HTTPServer(('127.0.0.1', port), QuietHandler)
    print(f"\n[🚀] Live Dev Server running at: http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
    finally:
        server.server_close()

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"

    if cmd == "build":
        build_site()
    elif cmd == "serve":
        build_site()
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        serve_site(port=port)
    else:
        print("Usage:")
        print("  python minssg.py build       - Build markdown files to dist/")
        print("  python minssg.py serve [port]- Build and start local dev server")

if __name__ == "__main__":
    main()
