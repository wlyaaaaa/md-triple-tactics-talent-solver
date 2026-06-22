# -*- coding: utf-8 -*-
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ==========================================
# 核心配置文件
# ==========================================
SOURCE_IMAGE_FILE = "image_4.png"  # 原始背景图
OUTPUT_16_9_FILE = "cover_v2_16_9.png" # 16:9 2.0 终极科技版
OUTPUT_4_3_FILE = "cover_v2_4_3.png"   # 4:3 2.0 终极科技版

# 核心文案（2.0）
TEXT_LINE1 = "三战之才2.0"
TEXT_LINE2 = "白嫖376钻"
TEXT_SUB = "1亿次模拟 · 95%保底210 · 直接抄"

# 科技感配色
COLOR_CYAN_NEON = (34, 211, 238, 255)  # 霓霓青（边框与装饰线条）
CYAN_START = (220, 252, 255)           # 第一行文字：极地冰晶蓝
CYAN_END = (34, 180, 210)              # 第一行文字：深邃科幻蓝

COLOR_GOLD_START = (255, 230, 130)     # 第二行文字：香槟金
COLOR_GOLD_END = (245, 150, 20)        # 第二行文字：琥珀橙

COLOR_WHITE = (245, 247, 250, 255)     # 数据槽文字颜色
SHADOW_COLOR = (8, 12, 18)             # 阴影融合色

# 兼容性处理：Resampling 过滤器
try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.ANTIALIAS

# ==========================================
# 辅助函数
# ==========================================
def get_best_chinese_font(size=40):
    fonts_to_try = [
        "Noto Sans CJK SC Bold", "Source Han Sans SC Bold", "msyh.ttc", "msyh.ttf",
        "SimHei.ttf", "Arial Unicode MS.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
    ]
    for file in os.listdir('.'):
        if file.lower().endswith(('.ttf', '.ttc')):
            fonts_to_try.insert(0, file)
    for font_name in fonts_to_try:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_gradient_text(base_img, text, font, xy, col_start, col_end, shadow_offset=(6, 6), shadow_blur=5):
    """
    绘制带有软阴影和垂直渐变的高级艺术字
    """
    x, y = xy
    draw_temp = ImageDraw.Draw(base_img)
    try:
        left, top, right, bottom = draw_temp.textbbox((0, 0), text, font=font)
        w, h = right - left, bottom - top
    except AttributeError:
        w, h = draw_temp.textsize(text, font=font)
        left, top = 0, 0
        
    pad = 20
    tw, th = w + pad * 2, h + pad * 2
    
    text_mask = Image.new("L", (tw, th), 0)
    mask_draw = ImageDraw.Draw(text_mask)
    mask_draw.text((pad - left, pad - top), text, font=font, fill=255)
    
    grad_img = Image.new("RGBA", (tw, th))
    grad_draw = ImageDraw.Draw(grad_img)
    for row in range(th):
        t = row / max(1, th - 1)
        r = int(col_start[0] + (col_end[0] - col_start[0]) * t)
        g = int(col_start[1] + (col_end[1] - col_start[1]) * t)
        b = int(col_start[2] + (col_end[2] - col_start[2]) * t)
        grad_draw.line([(0, row), (tw, row)], fill=(r, g, b, 255))
        
    shadow_mask = text_mask.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    shadow_layer = Image.new("RGBA", (tw, th), (SHADOW_COLOR[0], SHADOW_COLOR[1], SHADOW_COLOR[2], 220))
    
    final_text_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    final_text_layer.paste(shadow_layer, (x - pad + shadow_offset[0], y - pad + shadow_offset[1]), mask=shadow_mask)
    final_text_layer.paste(grad_img, (x - pad, y - pad), mask=text_mask)
    
    return Image.alpha_composite(base_img, final_text_layer)


def draw_procedural_flame(base_img, x, y, size=60):
    """
    超采样发光火苗
    """
    ss_scale = 4
    ss_size = size * ss_scale
    ss_canvas = Image.new("RGBA", (ss_size, ss_size), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(ss_canvas)
    
    def scale_pts(pts):
        return [(int(p[0] * ss_size / 100), int(p[1] * ss_size / 100)) for p in pts]
    
    outer_pts = [(50, 5), (63, 23), (76, 42), (83, 64), (74, 86), (50, 96), (26, 86), (17, 64), (24, 42), (37, 23)]
    mid_pts = [(50, 20), (60, 36), (69, 52), (72, 68), (64, 83), (50, 90), (36, 83), (28, 68), (31, 52), (40, 36)]
    inner_pts = [(50, 42), (56, 54), (62, 67), (57, 81), (50, 86), (43, 81), (38, 67), (44, 54)]
    
    glow_mask = Image.new("L", (ss_size, ss_size), 0)
    glow_draw = ImageDraw.Draw(glow_mask)
    glow_draw.polygon(scale_pts(outer_pts), fill=255)
    glow_mask_blurred = glow_mask.filter(ImageFilter.GaussianBlur(radius=6 * ss_scale))
    
    glow_color_layer = Image.new("RGBA", (ss_size, ss_size), (255, 69, 0, 160))
    ss_canvas.paste(glow_color_layer, (0, 0), mask=glow_mask_blurred)
    
    ss_draw.polygon(scale_pts(outer_pts), fill=(255, 69, 0, 255))
    ss_draw.polygon(scale_pts(mid_pts), fill=(255, 140, 0, 255))
    ss_draw.polygon(scale_pts(inner_pts), fill=(255, 225, 30, 255))
    
    flame_final = ss_canvas.resize((size, size), RESAMPLE_FILTER)
    base_img.paste(flame_final, (x, y), mask=flame_final)
    return base_img


def draw_cyber_ui_panel(base_img, px1, py1, px2, py2):
    """
    绘制轻量化全息暗色面板（不透明度从225降低到165，呈现高端通透感）
    """
    panel_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel_layer)
    
    # 科技感切角坐标
    chamfer = 45
    pts = [
        (px1 + chamfer, py1),
        (px2, py1),
        (px2, py2 - chamfer),
        (px2 - chamfer, py2),
        (px1, py2),
        (px1, py1 + chamfer)
    ]
    
    # 填充半透明全息暗蓝（不透明度设为165，使背景隐约可见，极具高级层次感）
    draw.polygon(pts, fill=(8, 12, 21, 165))
    
    # 绘制霓霓边框
    draw.polygon(pts, outline=COLOR_CYAN_NEON, width=3)
    
    # 绘制 HUD 点缀线
    draw.rectangle([(px1 + 50, py1 + 15), (px1 + 130, py1 + 22)], fill=COLOR_CYAN_NEON)
    draw.line([(px1 + 30, py2 - 25), (px1 + 80, py2 - 25)], fill=COLOR_CYAN_NEON, width=4)
    
    # 角隅十字准星装饰 (+)
    cross_size = 8
    def draw_cross(cx, cy):
        draw.line([(cx - cross_size, cy), (cx + cross_size, cy)], fill=COLOR_CYAN_NEON, width=2)
        draw.line([(cx, cy - cross_size), (cx, cy + cross_size)], fill=COLOR_CYAN_NEON, width=2)
    
    draw_cross(px2 - 30, py1 + 30)
    
    return Image.alpha_composite(base_img, panel_layer)

# ==========================================
# 主生成逻辑
# ==========================================
def make_cyber_cover(aspect_ratio="16_9"):
    print(f"\n[+] 正在渲染 B 站特供 [{aspect_ratio}] 数据舱封面...")
    
    try:
        raw_img = Image.open(SOURCE_IMAGE_FILE).convert("RGBA")
    except FileNotFoundError:
        print(f"[-] 错误: 找不到 '{SOURCE_IMAGE_FILE}'")
        sys.exit(1)
        
    # 极致清晰：直接采用 LANCZOS 高清重采样，不再施加任何模糊滤镜
    base_img = raw_img.resize((1920, 1080), RESAMPLE_FILTER)
    
    # 布局定位
    if aspect_ratio == "16_9":
        width, height = 1920, 1080
        # 优化面板：收窄至 800 像素，给右侧闪刀姬留出更多呼吸空间
        px1, py1, px2, py2 = 80, 150, 880, 930
        text_x = px1 + 60
        y_line1 = py1 + 130
        y_line2 = py1 + 320
        y_badge = py2 - 170
        
        font_size_l1 = 110  # 稍微缩减字号以配合瘦身后的面板
        font_size_l2 = 135
        font_size_sub = 36
        flame_size = 42
        output_file = OUTPUT_16_9_FILE
        
    elif aspect_ratio == "4_3":
        width, height = 1440, 1080
        crop_left = (1920 - width) // 2
        base_img = base_img.crop((crop_left, 0, crop_left + width, height))
        
        # 4:3 比例优化：将面板收窄至 660 像素，大幅扩宽右侧角色展示区
        px1, py1, px2, py2 = 60, 150, 720, 930
        text_x = px1 + 50
        y_line1 = py1 + 130
        y_line2 = py1 + 300
        y_badge = py2 - 170
        
        font_size_l1 = 95
        font_size_l2 = 115
        font_size_sub = 32
        flame_size = 38
        output_file = OUTPUT_4_3_FILE
    else:
        return

    # 加载字体
    font_l1 = get_best_chinese_font(font_size_l1)
    font_l2 = get_best_chinese_font(font_size_l2)
    font_sub = get_best_chinese_font(font_size_sub)

    # 1. 铺设科技感 HUD 数据舱面板
    base_img = draw_cyber_ui_panel(base_img, px1, py1, px2, py2)

    # 2. 绘制第一行文案（极地冰晶蓝渐变）
    base_img = draw_gradient_text(
        base_img, TEXT_LINE1, font_l1, (text_x, y_line1), CYAN_START, CYAN_END
    )

    # 3. 绘制第二行核心爽点（香槟金渐变）
    base_img = draw_gradient_text(
        base_img, TEXT_LINE2, font_l2, (text_x, y_line2), COLOR_GOLD_START, COLOR_GOLD_END
    )

    # 4. 绘制底部数据芯片
    draw = ImageDraw.Draw(base_img)
    badge_w = px2 - px1 - 100
    badge_h = 75
    bx1, by1 = text_x, y_badge
    bx2, by2 = bx1 + badge_w, by1 + badge_h
    
    # 绘制深灰色数据槽底板与霓霓边线
    draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=15, fill=(15, 23, 42, 255), outline=COLOR_CYAN_NEON, width=2)
    
    # 绘制发光火苗
    base_img = draw_procedural_flame(base_img, bx1 + 25, by1 + (badge_h - flame_size)//2, size=flame_size)
    
    # 绘制芯片内数据描述
    draw_temp = ImageDraw.Draw(base_img)
    draw_temp.text((bx1 + 25 + flame_size + 15, by1 + 18), TEXT_SUB, font=font_sub, fill=(255, 255, 255, 255))

    # 5. 保存
    base_img.convert("RGB").save(output_file, quality=95)
    print(f"[=] 高清高质感科技海报已存盘: {output_file}")


if __name__ == "__main__":
    make_cyber_cover("16_9")
    make_cyber_cover("4_3")
    print("\n[+] 重新渲染完成！背景图已完美恢复清晰，面板层次感倍增，请检查效果！")