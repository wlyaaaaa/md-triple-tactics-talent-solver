# -*- coding: utf-8 -*-
"""
报告 PDF → 横屏整页高清 PNG
============================
把 三战之才2.0纠错版策略报告.pdf（本就是 A4 横屏）每页渲成高清 PNG，
整页原样、不裁不套框，作为片尾「相关文档」翻页素材。
输出 WCS/v2_frames/doc_p01.png …
"""
import os
import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "v2_frames")
os.makedirs(OUT, exist_ok=True)


def find_pdf():
    for p in ("三战之才2.0纠错版策略报告.pdf", os.path.join("..", "三战之才2.0纠错版策略报告.pdf")):
        fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.exists(fp):
            return fp
    raise FileNotFoundError("报告 PDF 未找到")


def main():
    pdf = find_pdf()
    doc = fitz.open(pdf)
    zoom = 3.5  # ≈ 252 DPI
    mat = fitz.Matrix(zoom, zoom)
    n = 0
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out = os.path.join(OUT, f"doc_p{i:02d}.png")
        pix.save(out)
        n += 1
        print(f"  doc_p{i:02d}.png  {pix.width}x{pix.height}")
    doc.close()
    print(f"[+] 共 {n} 页 → {OUT}")


if __name__ == "__main__":
    main()
