# -*- coding: utf-8 -*-
"""
TimeAudit 文档 PDF 生成器
=========================
把 README.md / 快速部署.md / 使用手册.md 转成排版精良、中文友好的 PDF。
原理：Markdown → 内嵌中文字体样式的 HTML → 用系统自带的 Microsoft Edge 无头模式打印成 PDF。
直接运行： python build_docs_pdf.py
依赖： pip install markdown （以及 Windows 自带的 Edge）
"""
import os, sys, subprocess, tempfile, shutil
import markdown

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = ["README.md", "快速部署.md", "使用手册.md"]

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

CSS = """
/* ── 白色 · 纯绿 · 高级感主题（emerald on white）─────────────────── */
@page { size: A4 landscape; margin: 1.2cm 1.2cm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Microsoft YaHei","微软雅黑","Segoe UI",-apple-system,sans-serif;
       font-size: 12px; line-height: 1.78; color: #1b2a22; letter-spacing: .1px; background: #fff; }

h1 { font-size: 25px; font-weight: 700; color: #0b6b3a; letter-spacing: .3px;
     margin: 0 0 18px; padding: 0 0 10px; border-bottom: 2px solid #16a34a; }
h2 { font-size: 18px; font-weight: 650; color: #0e7c43; margin: 26px 0 10px;
     padding: 2px 0 2px 12px; border-left: 4px solid #16a34a; }
h3 { font-size: 14.5px; font-weight: 650; color: #11885a; margin: 18px 0 6px; }
h4 { font-size: 12.5px; font-weight: 650; color: #2f4a3c; margin: 14px 0 4px; }
h1, h2, h3, h4 { page-break-after: avoid; }

p, li { margin: 5px 0; }
strong { color: #0b6b3a; }
a { color: #15925f; text-decoration: none; border-bottom: 1px solid #bfe8d2; }
ul, ol { padding-left: 22px; }
li::marker { color: #16a34a; }
hr { border: none; border-top: 1px solid #d7eee2; margin: 18px 0; }
img { max-width: 100%; }

table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10.6px;
        border: 1px solid #d7eee2; }
th { background: #0e7c43; color: #fff; font-weight: 600; text-align: left;
     padding: 7px 10px; letter-spacing: .2px; }
td { border-top: 1px solid #e4f3ea; padding: 6px 10px; vertical-align: top; color: #28382f; }
tr:nth-child(even) td { background: #f4fbf6; }
tr, td, th { page-break-inside: avoid; }

code { background: #ecfdf3; color: #0b6b3a; padding: 1.5px 5px; border-radius: 4px;
       font-family: "Cascadia Code",Consolas,"Courier New",monospace; font-size: 11px; }
pre { background: #f6fdf9; border: 1px solid #d7eee2; border-left: 3px solid #16a34a;
      border-radius: 6px; padding: 12px 14px; overflow-x: auto;
      page-break-inside: avoid; margin: 10px 0; }
pre code { background: none; color: #1f3a2b; padding: 0; }

blockquote { border-left: 3px solid #22c55e; background: #f0fbf4; margin: 10px 0;
             padding: 7px 16px; color: #3a4a42; border-radius: 0 6px 6px 0; }
"""

HTML_TMPL = "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>" \
            "<style>{css}</style></head><body>{body}</body></html>"


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def md_to_pdf(edge, md_path, pdf_path, html_dir):
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists", "toc"])
    html = HTML_TMPL.format(css=CSS, body=body)
    html_path = os.path.join(html_dir, "_pdfbuild_tmp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    file_url = "file:///" + html_path.replace("\\", "/")
    # 关键：必须经 PowerShell 的 Start-Process -Wait 启动 Edge。直接用 Python subprocess 调 Edge，
    # 在已有 Edge 实例运行时会被"单例转发"机制抢走、自身空转退出 → 只产出空白 PDF。
    # 独立 user-data-dir + --no-first-run 隔离用户配置；html 放项目目录规避 headless 的 file:// 限制。
    prof = tempfile.mkdtemp(prefix="edge_pdf_")
    args = ("'--headless=new','--disable-gpu','--no-first-run','--no-pdf-header-footer',"
            "'--user-data-dir={prof}','--print-to-pdf={pdf}','{url}'").format(
                prof=prof, pdf=pdf_path, url=file_url)
    ps = ("$p=Start-Process -FilePath '{edge}' -ArgumentList {args} "
          "-PassThru -Wait -WindowStyle Hidden; exit $p.ExitCode").format(edge=edge, args=args)
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       timeout=120, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        try:
            os.unlink(html_path)
        except Exception:
            pass
        shutil.rmtree(prof, ignore_errors=True)
    return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert Markdown files to PDF using Edge headless mode.")
    parser.add_argument("--dir", default=ROOT, help="Working directory containing the markdown files")
    parser.add_argument("--docs", nargs="+", default=None, help="List of markdown files to convert")
    parser.add_argument("--git", action="store_true", help="Add, commit, and push generated PDFs to GitHub")
    args = parser.parse_args()

    edge = find_edge()
    if not edge:
        print("❌ 未找到 Edge/Chrome，无法生成 PDF")
        return 1
    print("使用浏览器内核:", edge)

    target_dir = os.path.abspath(args.dir)
    if args.docs is not None:
        docs = args.docs
    else:
        if target_dir == ROOT:
            docs = DOCS
        else:
            docs = [f for f in os.listdir(target_dir) if f.lower().endswith(".md") and not f.startswith("_")]
            if not docs:
                print(f"❌ 未在目录 {target_dir} 中找到 markdown 文件")
                return 1

    ok = 0
    generated_pdfs = []
    for md in docs:
        md_path = os.path.join(target_dir, md)
        if not os.path.exists(md_path):
            print(f"  ⚠️ 跳过(不存在): {md}")
            continue
        pdf_path = os.path.join(target_dir, os.path.splitext(md)[0] + ".pdf")
        if md_to_pdf(edge, md_path, pdf_path, target_dir):
            print(f"  ✅ {md} → {os.path.basename(pdf_path)}  ({os.path.getsize(pdf_path)//1024} KB)")
            ok += 1
            generated_pdfs.append(pdf_path)
        else:
            print(f"  ❌ 生成失败: {md}")

    print(f"完成：{ok}/{len(docs)} 个 PDF")

    if args.git and ok > 0:
        print("🚀 正在将 PDF 自动上传到 GitHub...")
        pdf_names = [os.path.basename(p) for p in generated_pdfs]
        try:
            for pdf in pdf_names:
                subprocess.run(["git", "add", pdf], cwd=target_dir, check=True)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=target_dir, capture_output=True, text=True, check=True)
            has_changes = False
            for line in status.stdout.splitlines():
                line = line.strip()
                if any(pdf in line for pdf in pdf_names):
                    has_changes = True
                    break

            if has_changes:
                commit_msg = f"docs: auto-generate PDFs for {', '.join(pdf_names)}"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=target_dir, check=True)
                subprocess.run(["git", "push"], cwd=target_dir, check=True)
                print("✅ 成功推送 PDF 到 GitHub!")
            else:
                print("ℹ️ 无更新，PDF 文件内容未发生变化，无需推送。")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 操作失败: {e}")
            return 1

    return 0 if ok == len(docs) else 1


if __name__ == "__main__":
    sys.exit(main())
