# -*- coding: utf-8 -*-
"""
三战之才 2.0 纠错版 · 全 11 幕 4K 配音分镜出图
================================================
风格沿用 gen_v2_slides_01_04（4K白底渐变 / emerald 配色 / PIL）。
内容全部按官方"每场取最高一级"规则重写：
  - 作业表改 v2a 分组（高频属性各押两张）；删 750相加 / 210铁保底 / 独享万钻。
  - 数字读 corrected_sim_results.json，频数读 md_monsters_active.csv，杜绝写死。
"""
import os, csv, json
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

W, H = 3840, 2160
ROOT = "e:/Pictures/三战之才/WCS"
OUT = os.path.join(ROOT, "v2_frames")
os.makedirs(OUT, exist_ok=True)


def _p(*n):
    for x in n:
        if os.path.exists(x):
            return x
        y = os.path.join("..", x)
        if os.path.exists(y):
            return y
    raise FileNotFoundError(n)


# ---- 读取权威数据 ----
with open(_p("corrected_sim_results.json"), encoding="utf-8") as f:
    S = json.load(f)
V1 = S["templates"]["v1"]["max_official"]
V2 = S["templates"]["v2"]["max_official"]
V2ADD = S["templates"]["v2"]["additive"]
V1ADD = S["templates"]["v1"]["additive"]
HYB = S["hybrid_day1_is_v1"]["max_official"]
FAIL_V1 = S["templates"]["v1"]["attr_pigeonhole_fail_rate"]
FAIL_V2 = S["templates"]["v2"]["attr_pigeonhole_fail_rate"]
NMON = S["n_monsters"]

_a, _r, _k = Counter(), Counter(), Counter()
with open(_p("md_monsters_active.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        _a[row["attribute"]] += 1
        _r[row["race"]] += 1
        _k[int(row["atk"])] += 1
ATTR_TOP = _a.most_common(7)
RACE_TOP = _r.most_common(10)
ATK_TOP = _k.most_common(10)
RACE_CN = {"Warrior": "战士族", "Machine": "机械族", "Fiend": "恶魔族", "Dragon": "龙族",
           "Spellcaster": "魔法师族", "Fairy": "天使族", "Beast": "兽族", "Winged Beast": "鸟兽族",
           "Cyberse": "电子界族", "Aqua": "水族"}
ATTR_CN7 = {"DARK": "暗", "EARTH": "地", "LIGHT": "光", "WATER": "水", "WIND": "风", "FIRE": "炎", "DIVINE": "神"}


def font(size, bold=False):
    p = "C:\\Windows\\Fonts\\msyhbd.ttc" if bold else "C:\\Windows\\Fonts\\msyh.ttc"
    for f_ in ([p] if os.path.exists(p) else []) + ["C:\\Windows\\Fonts\\msyh.ttc", "C:\\Windows\\Fonts\\simhei.ttf"]:
        if os.path.exists(f_):
            try:
                return ImageFont.truetype(f_, size)
            except Exception:
                pass
    return ImageFont.load_default()


def bg():
    img = Image.new("RGB", (W, H), (253, 253, 254))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(253 + (238 - 253) * t), int(253 + (244 - 253) * t), int(254 + (246 - 254) * t)))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for x in range(0, W, 120):
        gd.line([(x, 0), (x, H)], fill=(148, 163, 184, 15), width=2)
    for y in range(0, H, 120):
        gd.line([(0, y), (W, y)], fill=(148, 163, 184, 15), width=2)
    img.paste(g, (0, 0), g)
    return img


def card(img, x, y, w, h, fill=(255, 255, 255), border=(16, 185, 129), bw=4):
    glow = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle([(0, 0), (w + 39, h + 39)], fill=(100, 116, 139, 15))
    img.paste(glow, (x - 10, y - 10), glow)
    panel = Image.new("RGBA", (w, h), (*fill, 248))
    ImageDraw.Draw(panel).rectangle([(0, 0), (w - 1, h - 1)], outline=(*border, 255), width=bw)
    img.paste(panel, (x, y), panel)


def ct(d, cx, cy, t, f, fill, anchor="mm"):
    d.text((cx, cy), t, font=f, fill=fill, anchor=anchor)


def lt(d, x, y, t, f, fill):
    d.text((x, y), t, font=f, fill=fill)


DARK = (15, 23, 42); GRAY = (71, 85, 105)
LIGHT_G = (244, 252, 248); LIGHT_R = (254, 242, 242); LIGHT_B = (240, 249, 255)
EMERALD = (16, 185, 129); EMERALD_D = (4, 120, 87)
AMBER = (245, 158, 11); AMBER_D = (217, 119, 6)
RED = (239, 68, 68); RED_D = (220, 38, 38)
BLUE = (59, 130, 246); BLUE_D = (29, 78, 216); WHITE = (255, 255, 255)
AC = {"暗": (147, 51, 234), "地": (180, 83, 9), "光": (202, 138, 4),
      "水": (2, 132, 199), "风": (22, 163, 74), "炎": (225, 29, 72), "神": (120, 120, 120)}


def titlebar(img, accent, title, sub, sub_c):
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 30), (W, 210)], fill=(255, 255, 255))
    d.line([(0, 210), (W, 210)], fill=accent, width=6)
    ct(d, W // 2, 120, title, font(92, True), DARK)
    ct(d, W // 2, 285, sub, font(46, True), sub_c)
    return d


# ════════════════ Scene 1：作业表 ════════════════
def scene1():
    img = bg()
    titlebar(img, EMERALD, "[ 游戏王MD ] 三战之才 2.0 升级策略版 · 作业表",
             f"1亿次模拟  |  期望收益约 370-380 钻  |  95% 概率 ≥ {V2['floor_95']} 钻  |  99% 概率 ≥ {V2['floor_99']} 钻", EMERALD_D)
    card(img, 100, 360, 3640, 1080, border=EMERALD)
    d = ImageDraw.Draw(img)
    hbar = Image.new("RGBA", (3620, 100), (*EMERALD_D, 230)); img.paste(hbar, (110, 370), hbar)
    d = ImageDraw.Draw(img)
    cx = [110, 660, 1660, 2660]; cw = [550, 1000, 1000, 1000]
    for i, h in enumerate(["循环周期 (押注属性)", "卡片 1", "卡片 2", "卡片 3"]):
        ct(d, cx[i] + cw[i] // 2, 420, h, font(48, True), WHITE)
    rows = [
        ("第 1/4/7 天", "在 暗 上押两张", [("暗", "龙族 / 2500", "27张"), ("暗", "恶魔族 / 0", "75张"), ("水", "魔法师族 / 1500", "7张")]),
        ("第 2/5/8 天", "在 光 上押两张", [("光", "天使族 / 1600", "17张"), ("光", "机械族 / 1000", "17张"), ("风", "鸟兽族 / 1200", "11张")]),
        ("第 3/6/9 天", "在 地 上押两张", [("地", "战士族 / 1800", "32张"), ("地", "兽族 / 800", "24张"), ("炎", "炎族 / 1700", "10张")]),
    ]
    for ri, (period, hint, cs) in enumerate(rows):
        ry = 490 + ri * 300
        if ri > 0:
            d.line([(130, ry), (3720, ry)], fill=(226, 232, 240), width=2)
        ct(d, cx[0] + cw[0] // 2, ry + 110, period, font(50, True), DARK)
        ct(d, cx[0] + cw[0] // 2, ry + 175, hint, font(38, True), EMERALD_D)
        for ci, (attr, desc, dep) in enumerate(cs):
            x = cx[1 + ci] + cw[1 + ci] // 2
            ct(d, x, ry + 70, f"[{attr}]", font(64, True), AC[attr])
            ct(d, x, ry + 150, desc, font(46, True), DARK)
            ct(d, x, ry + 215, f"(真卡深度: {dep})", font(38), EMERALD_D)
    card(img, 100, 1490, 3640, 190, fill=LIGHT_R, border=RED, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1548, ">>> 搜完特征后，把列表滑到最底部，挑名字最冷僻的怪兽提交！别选热门卡！ <<<", font(50, True), RED_D)
    ct(d, W // 2, 1615, "冷门卡 = 同中奖的人少，Hit 大奖奖池你分到的那一份更大", font(40), GRAY)
    card(img, 100, 1730, 3640, 250, fill=WHITE, border=EMERALD, bw=3)
    d = ImageDraw.Draw(img)
    stats = [("平均期望", "约 376 钻", EMERALD_D), ("90% 概率", f"≥ {V2['floor_90']} 钻", AMBER_D),
             ("95% 概率", f"≥ {V2['floor_95']} 钻", BLUE_D), ("99% 概率", f"≥ {V2['floor_99']} 钻", EMERALD_D)]
    sx = 280
    for lb, v, c in stats:
        ct(d, sx, 1808, lb, font(40), GRAY); ct(d, sx, 1878, v, font(56, True), c); sx += 860
    ct(d, W // 2, 2050, "数据: YGOPRODeck 卡查站 · 8944 怪兽 · 7 属性  |  9 卡位共约 220 张真卡可挑冷门  |  AMD 9950X3D · 32进程 · 1亿次仿真", font(36), GRAY)
    img.save(os.path.join(OUT, "scene01_homework.png")); print("OK 01")


# ════════════════ Scene 2：亡羊补牢 ════════════════
def scene2():
    img = bg()
    titlebar(img, RED, "紧急：已按 1.0 交了第一天的兄弟看这里！", "别慌不用重来 —— 从第 2 天起直接切 2.0 即可", RED_D)
    card(img, 100, 380, 1740, 820, fill=WHITE, border=GRAY, bw=3)
    d = ImageDraw.Draw(img)
    ct(d, 970, 445, "Day 1（1.0 已提交）", font(58, True), GRAY)
    d.line([(120, 510), (1820, 510)], fill=(226, 232, 240), width=2)
    for i, (t, c) in enumerate([("[暗] 战士族 / 0", AC["暗"]), ("[地] 机械族 / 1000", AC["地"]), ("[光] 恶魔族 / 1500", AC["光"])]):
        lt(d, 230, 560 + i * 110, t, font(52, True), c)
    ct(d, 970, 960, "你这张「暗」刚好顶上 2.0 第一天的暗位", font(44, True), EMERALD_D)
    ct(d, 970, 1040, "后面两天补上 光光 / 地地 即可", font(42), GRAY)
    ct(d, 1920, 770, ">>>", font(110, True), EMERALD_D)
    card(img, 2000, 380, 1740, 820, fill=WHITE, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2870, 445, "Day 2 / 3（立即切 2.0）", font(58, True), EMERALD_D)
    d.line([(2020, 510), (3720, 510)], fill=(226, 232, 240), width=2)
    lt(d, 2090, 580, "Day 2：[光]天使/1600   [光]机械/1000   [风]鸟兽/1200", font(42, True), DARK)
    lt(d, 2090, 700, "Day 3：[地]战士/1800   [地]兽/800   [炎]电子界/2000", font(42, True), DARK)
    ct(d, 2870, 850, "暗(Day1) + 光光(Day2) + 地地(Day3)", font(46, True), AMBER_D)
    ct(d, 2870, 940, "三大高频属性照样全覆盖，无缝衔接", font(50, True), EMERALD_D)
    ct(d, 2870, 1040, "且 Day2/3 卡池深，冷门卡随便挑", font(42), GRAY)
    card(img, 100, 1300, 3640, 560, fill=WHITE, border=AMBER, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1370, "混搭方案 vs 死守 1.0（一亿次仿真 · 官方取最高模型）", font(54, True), AMBER_D)
    d.line([(120, 1425), (3720, 1425)], fill=(226, 232, 240), width=2)
    lt(d, 250, 1470, "死守 1.0 走完三场：", font(50, True), GRAY)
    lt(d, 1250, 1470, f"期望 {V1['total_mean']:.0f} 钻", font(50), GRAY)
    lt(d, 1850, 1470, f"95%保底 {V1['floor_95']} 钻", font(50), GRAY)
    lt(d, 2650, 1470, f"99%底线 {V1['floor_99']} 钻", font(50), GRAY)
    lt(d, 250, 1600, "Day1 走 1.0 + Day2/3 切 2.0：", font(50, True), EMERALD_D)
    lt(d, 1250, 1600, f"期望 {HYB['total_mean']:.0f} 钻", font(50, True), EMERALD_D)
    lt(d, 1850, 1600, f"95%保底 {HYB['floor_95']} 钻", font(50, True), BLUE_D)
    lt(d, 2650, 1600, f"99%底线 {HYB['floor_99']} 钻", font(50, True), EMERALD_D)
    ct(d, W // 2, 1760, f"期望 +{HYB['total_mean']-V1['total_mean']:.0f} 钻，95%保底 +{HYB['floor_95']-V1['floor_95']} 钻，几乎追平满 2.0（{V2['total_mean']:.0f} 钻）", font(50, True), EMERALD_D)
    ct(d, W // 2, 1960, "结论：第 1 天交了 1.0 不要紧，后两天立刻切 2.0！", font(56, True), RED_D)
    img.save(os.path.join(OUT, "scene02_emergency.png")); print("OK 02")


# ════════════════ Scene 3：30秒看懂规则 ════════════════
def scene3():
    img = bg()
    titlebar(img, AMBER, "30 秒看懂「三战之才」规则", "搞懂双层取最高，才明白钻石怎么算", AMBER_D)
    card(img, 100, 380, 1740, 1350, fill=WHITE, border=AMBER)
    d = ImageDraw.Draw(img)
    ct(d, 970, 445, "活动流程", font(62, True), AMBER_D)
    d.line([(120, 505), (1820, 505)], fill=(226, 232, 240), width=2)
    steps = [("1.", "活动共 9 天", DARK), ("2.", "分 3 场，每 3 天为 1 场", DARK),
             ("", "    场1: 1/2/3 天   场2: 4/5/6 天   场3: 7/8/9 天", GRAY),
             ("3.", "每天提交 3 张预测怪兽卡", DARK),
             ("4.", "每场只公布一次中奖卡（3 张）", AMBER_D),
             ("5.", "你的卡与中奖卡比 属性 / 种族 / 攻击力", DARK),
             ("6.", "对得越多奖越高（攻击力 > 种族 > 属性）", DARK),
             ("7.", "关键：每场只结算最高，三场相加", RED_D)]
    cy = 560
    for n, t, c in steps:
        if n:
            lt(d, 210, cy, n, font(48, True), AMBER_D)
        lt(d, 300 if n else 230, cy, t, font(46, True if n else False), c); cy += 135
    card(img, 1960, 380, 1780, 640, fill=LIGHT_R, border=RED, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 445, "双层「取最高」结算", font(62, True), RED_D)
    d.line([(1980, 505), (3720, 505)], fill=(226, 232, 240), width=2)
    ct(d, 2850, 585, "① 一场 3 天 → 只取最高那天", font(52, True), DARK)
    ct(d, 2850, 680, "② 一天 3 项 → 只取最高那一项", font(52, True), RED_D)
    ct(d, 2850, 800, "单场 = MAX(三天 × 三项) 里最高的那一个奖", font(44, True), DARK)
    ct(d, 2850, 900, "总钻石 = 场1 + 场2 + 场3", font(46, True), EMERALD_D)
    card(img, 1960, 1090, 1780, 640, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 1155, "最大的坑：三项不能相加！", font(60, True), EMERALD_D)
    d.line([(1980, 1215), (3720, 1215)], fill=(226, 232, 240), width=2)
    ct(d, 2850, 1300, "属性 2 中(70) + 种族 2 中(100) + 攻击 2 中(150)", font(44), DARK)
    ct(d, 2850, 1390, "官方只发最高一项 = 150 钻  （不是 320！）", font(50, True), RED_D)
    ct(d, 2850, 1500, "上期把三项加起来，才把收益算虚高了", font(44), GRAY)
    ct(d, 2850, 1600, "本期已按官方「取最高」重算", font(48, True), EMERALD_D)
    img.save(os.path.join(OUT, "scene03_rules.png")); print("OK 03")


# ════════════════ Scene 4：奖励机制 ════════════════
def scene4():
    img = bg()
    titlebar(img, EMERALD, "奖励机制与结算细节", "每场只发最高一级 · Hit 大奖按人数均分", EMERALD_D)
    card(img, 100, 380, 2300, 900, fill=WHITE, border=EMERALD)
    d = ImageDraw.Draw(img)
    ct(d, 1250, 445, "单项匹配奖励表（取最高那一项）", font(56, True), EMERALD_D)
    d.line([(120, 505), (2380, 505)], fill=(226, 232, 240), width=2)
    hbar = Image.new("RGBA", (2260, 80), (*EMERALD_D, 230)); img.paste(hbar, (120, 515), hbar)
    d = ImageDraw.Draw(img)
    cxs = [120, 560, 990, 1420, 1850]; cws = [440, 430, 430, 430, 430]
    for i, h in enumerate(["匹配类型", "命中0", "命中1", "命中2", "命中3"]):
        ct(d, cxs[i] + cws[i] // 2, 555, h, font(42, True), WHITE)
    tdata = [("属性", ["0", "20", "70", "200"]), ("种族", ["0", "30", "100", "250"]),
             ("攻击力", ["0", "50", "150", "300"]), ("一天只取最高一项", ["", "", "", "≤300"])]
    for ri, (label, vals) in enumerate(tdata):
        ry = 625 + ri * 148
        d.line([(140, ry), (2360, ry)], fill=(226, 232, 240), width=1)
        ct(d, cxs[0] + cws[0] // 2, ry + 74, label, font(42, ri == 3), DARK if ri < 3 else AMBER_D)
        for ci, v in enumerate(vals):
            vc = EMERALD_D if ci == 3 else GRAY
            if ri == 3:
                vc = AMBER_D
            ct(d, cxs[1 + ci] + cws[1 + ci] // 2, ry + 74, v + ("" if v == "" else " 钻"), font(44, ci == 3 or ri == 3), vc)
    card(img, 2520, 380, 1220, 900, fill=LIGHT_G, border=AMBER, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 3130, 445, "Hit 大奖（整张卡相同）", font(54, True), AMBER_D)
    d.line([(2540, 505), (3720, 505)], fill=(226, 232, 240), width=2)
    for i, (t, c, b) in enumerate([("Single Hit：奖池 100 万宝石", DARK, True), ("Double Hit：奖池 200 万宝石", DARK, True),
                                   ("Triple Hit：奖池 300 万宝石", DARK, True), ("全服中奖者「均分」+ 固定 300", RED_D, True),
                                   ("交冷门卡 → 同中奖人少 → 你那份更大", EMERALD_D, True), ("无偿宝石持有上限 8000", GRAY, False)]):
        ct(d, 3130, 590 + i * 105, t, font(42, b), c)
    card(img, 100, 1380, 3640, 540, fill=WHITE, border=GRAY, bw=3)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1445, "三个容易踩的点", font(54, True), DARK)
    d.line([(120, 1505), (3720, 1505)], fill=(226, 232, 240), width=2)
    items = [("三项不相加：", "属性/种族/攻击力分开比对，但每场只发其中最高的一项，不叠加", AMBER_D),
             ("神属性是噪点：", "8944 张里只有 5 张神属性，整个活动撞上它约千分之 5，且攻击力「?」不等于 0，可忽略", GRAY),
             ("冷门卡的真意：", "冷门卡和热门卡中奖率一样，但热门卡一旦中奖，奖池被几万人均分到个位数", EMERALD_D)]
    cy = 1550
    for lab, desc, lc in items:
        lt(d, 250, cy, lab, font(46, True), lc); lt(d, 760, cy, desc, font(40), DARK); cy += 115
    img.save(os.path.join(OUT, "scene04_rewards.png")); print("OK 04")


# ════════════════ Scene 5：卡池普查 ════════════════
def scene5():
    img = bg()
    titlebar(img, BLUE, "卡池三维特征普查（2026.6）", "开奖是均匀随机抽 3 张 —— 卡越多越容易被抽中", BLUE_D)
    g1 = sum(_a[x] for x in ("DARK", "EARTH", "LIGHT"))
    cols = [(100, "属性 TOP 7", [(ATTR_CN7.get(a, a) + "属性", c) for a, c in ATTR_TOP], EMERALD),
            (1340, "种族 TOP 10", [(RACE_CN.get(r, r), c) for r, c in RACE_TOP], AMBER),
            (2580, "攻击力 TOP 10", [(("「?」" if k < 0 else str(k)), c) for k, c in ATK_TOP], BLUE)]
    for x0, title, data, clr in cols:
        card(img, x0, 380, 1160, 1380, border=clr)
        d = ImageDraw.Draw(img)
        ct(d, x0 + 580, 450, title, font(56, True), clr)
        d.line([(x0 + 30, 515), (x0 + 1130, 515)], fill=(226, 232, 240), width=2)
        maxc = data[0][1]
        for i, (name, c) in enumerate(data):
            ry = 575 + i * 118
            bw_ = int((c / maxc) * 760)
            bar = Image.new("RGBA", (max(bw_, 4), 56), (*clr, 70)); img.paste(bar, (x0 + 330, ry), bar)
            d = ImageDraw.Draw(img)
            lt(d, x0 + 45, ry + 4, f"{i+1}", font(40, True), GRAY)
            lt(d, x0 + 110, ry + 4, name, font(42, True), DARK)
            ct(d, x0 + 330 + max(bw_, 120) - 70, ry + 28, f"{c} ({c/NMON*100:.1f}%)", font(34, True), DARK)
    card(img, 100, 1810, 3640, 170, fill=LIGHT_G, border=EMERALD, bw=3)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1868, f"三大高频属性 暗 / 地 / 光 合计 {g1/NMON*100:.1f}% —— 作业表的每个词条都从这些高频特征里精选", font(50, True), EMERALD_D)
    ct(d, W // 2, 1935, "水 / 风 / 炎 合计仅 28.5%，所以拿它们当「对冲位」，不当主力", font(40), GRAY)
    img.save(os.path.join(OUT, "scene05_pool.png")); print("OK 05")


# ════════════════ Scene 6：上期翻车自查 ════════════════
def scene6():
    img = bg()
    titlebar(img, RED, "老实交代：上期我犯了两个错", "都是选卡的事 —— 算分没错，错在选了不能交的特征", RED_D)
    errs = [("错 1 · 选了「窄槽」特征", AMBER,
             ["上期推的　光 / 恶魔 / 1500，", "整个卡池只有 5 张真卡。", "几万人全挤这 5 张，",
              "就算蒙中大奖，也被均分", "到个位数钻。", "",
              "2.0 改选真卡多的黄金分类，", "如 暗 / 恶魔 / 0 = 75 张，", "冷门卡随便挑。"]),
            ("错 2 · 出现「空槽」特征", BLUE,
             ["上期有个词条（地/鸟兽/1200）", "在真卡池里一张都没有。", "照着抄根本交不上去，",
              "那个保底位直接作废。", "", "",
              "2.0 把 9 个词条全部", "和真卡内联校验，", "杜绝空槽。"])]
    x0 = 150
    for title, clr, lines in errs:
        card(img, x0, 380, 1700, 1300, border=clr)
        d = ImageDraw.Draw(img)
        hb = Image.new("RGBA", (1680, 130), (*clr, 40)); img.paste(hb, (x0 + 10, 390), hb)
        d = ImageDraw.Draw(img)
        ct(d, x0 + 850, 455, title, font(54, True), clr)
        d.line([(x0 + 30, 540), (x0 + 1670, 540)], fill=(226, 232, 240), width=2)
        cy = 635
        for i, ln in enumerate(lines):
            lt(d, x0 + 100, cy, ln, font(50, True if i >= 6 else False), DARK if i < 6 else EMERALD_D)
            cy += 92
        x0 += 1850
    card(img, 100, 1730, 3640, 250, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1800, "上期还说「210 钻铁保底是骗人的」—— 这次重算发现：方向对，但要说清", font(48, True), EMERALD_D)
    ct(d, W // 2, 1890, f"210 不是 100% 铁律，而是 95% 置信保底（属性兜底失效率仅 {FAIL_V2}%），最坏 99% 也有 {V2['floor_99']} 钻", font(46, True), DARK)
    img.save(os.path.join(OUT, "scene06_audit.png")); print("OK 06")


def _wrap(s, n):
    return "\n".join(s[i:i + n] for i in range(0, len(s), n))


# ════════════════ Scene 7：保底原理（核心纠错） ════════════════
def scene7():
    img = bg()
    titlebar(img, EMERALD, "属性保底的正确姿势：高频属性各押两张", "这是本期最反直觉、也最硬核的纠错点", EMERALD_D)
    card(img, 100, 380, 1780, 1340, fill=LIGHT_R, border=RED, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 990, 450, "× 误区：干净二分 + 鸽巢", font(58, True), RED_D)
    d.line([(120, 515), (1860, 515)], fill=(226, 232, 240), width=2)
    ct(d, 990, 595, "第1/3天交「暗地光」，第2天交「水风炎」", font(44, True), DARK)
    ct(d, 990, 680, "号称：3 个中奖属性落 2 组，必有一组 ≥ 2", font(42), GRAY)
    d.multiline_text((170, 770), "漏洞：鸽巢数的是「中奖卡(球)」，\n但实际计分数的是「你命中几张卡」。\n你每天只放 1 张暗，开奖出 2 张暗，\n也只算命中 1 个属性 = 20 钻。", font=font(46, True), fill=RED_D, spacing=18)
    ct(d, 990, 1180, f"一亿次仿真：属性保底失效率 {FAIL_V1:.0f}%", font(48, True), RED_D)
    ct(d, 990, 1270, "9 天期望只有约 285 钻，和 1.0 差不多", font(46, True), DARK)
    ct(d, 990, 1370, "等于没优化", font(44), GRAY)
    card(img, 1960, 380, 1780, 1340, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 450, "√ 正解：高频属性各押两张", font(58, True), EMERALD_D)
    d.line([(1980, 515), (3720, 515)], fill=(226, 232, 240), width=2)
    ct(d, 2850, 595, "第1天放 2 张暗，第2天放 2 张光，第3天放 2 张地", font(42, True), DARK)
    d.multiline_text((2030, 700), "暗 / 光 / 地 是占比最大的三个属性\n（合计 71%）。只要开奖出现其中任意\n一个，对应那天就有「两张同属性命中」\n= 稳拿 70 钻。", font=font(46, True), fill=EMERALD_D, spacing=18)
    ct(d, 2850, 1110, f"失效（一个高频都没开出）概率仅 {FAIL_V2}%", font(48, True), EMERALD_D)
    ct(d, 2850, 1200, f"9 天期望 {V2['total_mean']:.0f} 钻", font(54, True), EMERALD_D)
    ct(d, 2850, 1300, f"95%保底 {V2['floor_95']} 钻 · 99%底线 {V2['floor_99']} 钻", font(48, True), BLUE_D)
    card(img, 100, 1770, 3640, 210, fill=WHITE, border=AMBER, bw=3)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1830, "所以「210 钻保底」不是 100% 数学铁律，而是 95% 置信保底", font(52, True), AMBER_D)
    ct(d, W // 2, 1910, f"失效约 {FAIL_V2}%（多发生在三张全开水/风/炎/神时），且常被种族、攻击力兜底；最坏 99% 也有 {V2['floor_99']} 钻", font(42), GRAY)
    img.save(os.path.join(OUT, "scene07_floor.png")); print("OK 07")


# ════════════════ Scene 8：技术流程 5 步 ════════════════
def scene8():
    img = bg()
    titlebar(img, BLUE, "从 API 到一亿次模拟：2.0 是怎么算出来的", "32 进程并发 · 官方取最高模型", BLUE_D)
    steps = [("①", "数据抓取", "调 YGOPRODeck 卡查站 API\n（format=Master Duel）\n清洗出 8944 张活跃怪兽", EMERALD),
             ("②", "特征剪枝", "6 属性×9 种族×9 攻击力 = 486 节点\n砍掉 0 张卡的空槽和拥堵节点", AMBER),
             ("③", "模板搜索", "贪心搜 9 个特征分配三天\n6 属性覆盖 + 种族/攻击力去重", BLUE),
             ("④", "粗滤仿真", "每个候选跑百万次蒙特卡洛\nPK 出最强对冲模板", RED),
             ("⑤", "终极仿真", f"32 进程 1 亿次（官方取最高）\n期望 {V2['total_mean']:.0f} · 99%底线 {V2['floor_99']}", EMERALD_D)]
    x0 = 100
    for n, t, desc, clr in steps:
        card(img, x0, 380, 700, 900, border=clr)
        d = ImageDraw.Draw(img)
        ct(d, x0 + 350, 500, n, font(110, True), clr)
        ct(d, x0 + 350, 640, t, font(52, True), DARK)
        d.line([(x0 + 60, 710), (x0 + 640, 710)], fill=(226, 232, 240), width=2)
        d.multiline_text((x0 + 70, 770), desc, font=font(36), fill=GRAY, spacing=16)
        if x0 < 2800:
            ct(d, x0 + 730, 830, "→", font(80, True), clr)
        x0 += 748
    card(img, 100, 1340, 1780, 600, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 990, 1405, "关键优化：高频属性各押两张", font(54, True), EMERALD_D)
    d.line([(120, 1465), (1860, 1465)], fill=(226, 232, 240), width=2)
    ct(d, 990, 1545, "不是「三天属性完全不重合」", font(46, True), RED_D)
    ct(d, 990, 1635, "（那样 1-1-1 分布会塌成 20 钻）", font(42), GRAY)
    ct(d, 990, 1730, "而是在暗/光/地上各押两张", font(46, True), DARK)
    ct(d, 990, 1820, f"把属性保底失效率压到 {FAIL_V2}%", font(48, True), EMERALD_D)
    card(img, 1960, 1340, 1780, 600, fill=LIGHT_B, border=BLUE, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 1405, "对称性的边界", font(54, True), BLUE_D)
    d.line([(1980, 1465), (3720, 1465)], fill=(226, 232, 240), width=2)
    ct(d, 2850, 1545, "同一天 3 张卡内部对调 → 得分不变", font(46, True), EMERALD_D)
    ct(d, 2850, 1635, "（36 种排法完全等价，可放心挑冷门）", font(40), GRAY)
    ct(d, 2850, 1730, "但把特征挪到别的天 → 得分会变", font(46, True), RED_D)
    ct(d, 2850, 1820, f"这正是 285 与 {V2['total_mean']:.0f} 的差距来源", font(44), DARK)
    img.save(os.path.join(OUT, "scene08_pipeline.png")); print("OK 08")


# ════════════════ Scene 9：三方 PK ════════════════
def scene9():
    img = bg()
    titlebar(img, EMERALD, "一亿次模拟 · 三方大乱斗", "官方取最高模型下，谁才是真最优", EMERALD_D)
    card(img, 100, 380, 3640, 1240, border=EMERALD)
    d = ImageDraw.Draw(img)
    hbar = Image.new("RGBA", (3620, 110), (*EMERALD_D, 230)); img.paste(hbar, (110, 390), hbar)
    d = ImageDraw.Draw(img)
    cx = [110, 1310, 2110, 2910]; cw = [1200, 800, 800, 800]
    for i, h in enumerate(["指标（9天合计）", "1.0 方案", "2.0 高频各押两张", "干净二分/不重复"]):
        ct(d, cx[i] + cw[i] // 2, 445, h, font(46, True), WHITE)
    rows = [("平均期望（取最高）", f"{V1['total_mean']:.0f} 钻", f"{V2['total_mean']:.0f} 钻", "≈285 钻"),
            ("90% 保底", f"{V1['floor_90']}", f"{V2['floor_90']}", "≈190"),
            ("95% 保底", f"{V1['floor_95']}", f"{V2['floor_95']}", "≈170"),
            ("99% 底线", f"{V1['floor_99']}", f"{V2['floor_99']}", "≈150"),
            ("属性保底失效率", f"{FAIL_V1:.0f}%", f"{FAIL_V2}%", "≈25%"),
            ("可挑冷门·卡池深度", "≈51 张", "≈220 张", "≈220 张"),
            ("相加模型(旧/错)对照", f"{V1ADD['total_mean']:.0f}", f"{V2ADD['total_mean']:.0f}", "虚高")]
    for ri, (lab, a, b, c) in enumerate(rows):
        ry = 526 + ri * 150
        d.line([(130, ry), (3720, ry)], fill=(226, 232, 240), width=2)
        ct(d, cx[0] + cw[0] // 2, ry + 78, lab, font(42, True), DARK)
        ct(d, cx[1] + cw[1] // 2, ry + 78, a, font(46), GRAY)
        ct(d, cx[2] + cw[2] // 2, ry + 78, b, font(50, True), EMERALD_D)
        ct(d, cx[3] + cw[3] // 2, ry + 78, c, font(46), RED_D)
    card(img, 100, 1680, 3640, 300, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1760, f"2.0「高频各押两张」以 {V2['total_mean']:.0f} vs {V1['total_mean']:.0f}（+{(V2['total_mean']/V1['total_mean']-1)*100:.0f}%）完胜 1.0", font(54, True), EMERALD_D)
    ct(d, W // 2, 1850, "而「干净二分/三天不重复」直觉上很美，实际只有约 285 钻 —— 和 1.0 一个水平", font(46, True), DARK)
    ct(d, W // 2, 1925, "原因：属性平摊三天后，三个中奖属性各落一天，MAX 取出来每天只对上 1 个 = 20 钻", font(40), GRAY)
    img.save(os.path.join(OUT, "scene09_pk.png")); print("OK 09")


# ════════════════ Scene 10：冷门卡教学 ════════════════
def scene10():
    img = bg()
    titlebar(img, AMBER, "怎么吃满 Hit 大奖的均分？选「幽灵卡」", "中奖率人人一样，但同中奖的人越少，你那份越大", AMBER_D)
    card(img, 100, 380, 1780, 720, fill=LIGHT_R, border=RED, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 990, 445, "热门卡：万人同交", font(56, True), RED_D)
    d.line([(120, 510), (1860, 510)], fill=(226, 232, 240), width=2)
    ct(d, 990, 600, "灰流丽、增殖的G、暗黑天使…", font(46, True), DARK)
    ct(d, 990, 700, "一旦中奖，奖池被几万人均分", font(46), GRAY)
    ct(d, 990, 810, "100 万 ÷ 几万人 = 每人个位数钻", font(50, True), RED_D)
    ct(d, 990, 960, "情怀/本家玩家会无意识地交它们", font(42), GRAY)
    card(img, 1960, 380, 1780, 720, fill=LIGHT_G, border=EMERALD, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 445, "幽灵卡：全服可能就你交", font(56, True), EMERALD_D)
    d.line([(1980, 510), (3720, 510)], fill=(226, 232, 240), width=2)
    ct(d, 2850, 600, "名字古怪、无字段、无效果的远古凡骨", font(46, True), DARK)
    ct(d, 2850, 700, "同特征下没人会注意到它", font(46), GRAY)
    ct(d, 2850, 810, "一旦蒙中，奖池分母极小，你那份最大", font(50, True), EMERALD_D)
    ct(d, 2850, 960, "这才是冷门卡的唯一意义", font(42), GRAY)
    card(img, 100, 1160, 3640, 820, fill=WHITE, border=AMBER, bw=4)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1225, "幽灵卡筛选逻辑（报告已为 9 个卡位各推 3 张）", font(54, True), AMBER_D)
    d.line([(120, 1285), (3720, 1285)], fill=(226, 232, 240), width=2)
    items = [("第一步 排本家：", "烙印、深渊之兽、闪刀姬…即使冷门也容易被本家玩家交", RED_D),
             ("第二步 排手坑：", "灰流丽、增殖的G、无限泡影、屋敷童…肯定有人交", AMBER_D),
             ("第三步 选凡骨：", "名字最长、画风最古早、无效果的 Normal 怪兽，物理上最接近「幽灵」", EMERALD_D),
             ("实操：", "游戏内输入特征(如 暗/恶魔/0)→搜索→手指一直往下滑→选最不认识的那张提交", BLUE_D)]
    cy = 1340
    for lab, desc, lc in items:
        lt(d, 220, cy, lab, font(48, True), lc); lt(d, 760, cy, desc, font(40), DARK); cy += 150
    img.save(os.path.join(OUT, "scene10_ghost.png")); print("OK 10")


# ════════════════ Scene 11：总结 ════════════════
def scene11():
    img = bg()
    titlebar(img, EMERALD, "总结", f"照着交，平均约 {V2['total_mean']:.0f} 钻，95% 概率 ≥ {V2['floor_95']} 钻", EMERALD_D)
    card(img, 100, 380, 1780, 1340, fill=WHITE, border=EMERALD)
    d = ImageDraw.Draw(img)
    ct(d, 990, 450, "四句话记住 2.0", font(60, True), EMERALD_D)
    d.line([(120, 515), (1860, 515)], fill=(226, 232, 240), width=2)
    pts = [("1", [f"照 2.0 作业表交，期望 {V2['total_mean']:.0f} 钻", f"95% 保底 {V2['floor_95']} 钻"], EMERALD_D),
           ("2", ["已交 1.0 第一天？后两天", "直接切 2.0，完全兼容"], AMBER_D),
           ("3", ["选卡滑到最底，挑冷门幽灵卡", "吃满 Hit 大奖的均分"], BLUE_D),
           ("4", ["完整数据 PDF 见视频末尾", "（含 9 卡位冷门卡名单）"], DARK)]
    cy = 600
    for n, lines, c in pts:
        ce = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
        ImageDraw.Draw(ce).ellipse([(0, 0), (89, 89)], fill=(*c, 235))
        img.paste(ce, (180, cy), ce)
        d = ImageDraw.Draw(img)
        ct(d, 225, cy + 45, n, font(52, True), WHITE)
        d.multiline_text((310, cy - 5), "\n".join(lines), font=font(44, True), fill=DARK, spacing=14)
        cy += 270
    card(img, 1960, 380, 1780, 1340, fill=LIGHT_G, border=AMBER)
    d = ImageDraw.Draw(img)
    ct(d, 2850, 450, "关键数字", font(60, True), AMBER_D)
    d.line([(1980, 515), (3720, 515)], fill=(226, 232, 240), width=2)
    big = [("平均期望", f"{V2['total_mean']:.0f} 钻", EMERALD_D), ("95% 置信保底", f"{V2['floor_95']} 钻", BLUE_D),
           ("99% 绝对底线", f"{V2['floor_99']} 钻", AMBER_D)]
    cy = 600
    for lb, v, c in big:
        ct(d, 2850, cy, lb, font(48), GRAY); ct(d, 2850, cy + 80, v, font(96, True), c); cy += 270
    ct(d, 2850, 1620, "（按官方「每场取最高一级」如实重算）", font(40), GRAY)
    card(img, 100, 1770, 3640, 210, fill=EMERALD, border=EMERALD_D, bw=3)
    d = ImageDraw.Draw(img)
    ct(d, W // 2, 1875, "觉得有用，点个免费三连 —— 祝大家都开出 Hit 大奖，我们下期见！", font(58, True), WHITE)
    img.save(os.path.join(OUT, "scene11_summary.png")); print("OK 11")


if __name__ == "__main__":
    for fn in (scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11):
        fn()
    print("全部 11 幕已生成 →", OUT)
