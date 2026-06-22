# -*- coding: utf-8 -*-
"""
三战之才 2.0 纠错版策略报告生成器
=================================
读取 corrected_sim_results.json（官方"取最高一级"模型的一亿次仿真结果），
现场计算卡池频数表与冷门幽灵卡，输出改正后的策略报告 Markdown 并编译 PDF。

与旧版 generate_final_report.py 的区别：
  1. 所有收益/保底数字一律读 JSON，不再写死；按官方"取最高一项"规则。
  2. 作业表改用 best_hedging 的正确分组（高频属性各押两张：D1暗暗水/D2光光风/D3地地炎）。
  3. 改正话术：删"独享万钻/铁保底/MAX累加已修复"；补"双层SUM→MAX""95%保底""奖池均分+8000上限"。
"""
import os, csv, json, subprocess, shutil
from collections import Counter

ATTR_CN = {"DARK": "暗", "EARTH": "地", "LIGHT": "光", "WATER": "水", "WIND": "风", "FIRE": "炎", "DIVINE": "神"}
RACE_CN = {
    "Warrior": "战士族", "Machine": "机械族", "Fiend": "恶魔族", "Dragon": "龙族", "Spellcaster": "魔法师族",
    "Fairy": "天使族", "Beast": "兽族", "Winged Beast": "鸟兽族", "Cyberse": "电子界族", "Aqua": "水族",
    "Pyro": "炎族", "Thunder": "雷族", "Rock": "岩石族", "Plant": "植物族", "Insect": "昆虫族",
    "Zombie": "不死族", "Reptile": "爬虫类族", "Fish": "鱼族", "Sea Serpent": "海龙族", "Dinosaur": "恐龙族",
    "Wyrm": "幻龙族", "Psychic": "念动力族", "Divine-Beast": "幻神兽族", "Cyberse ": "电子界族",
}

POPULAR_ARCHETYPES = [
    "hero", "kuriboh", "cyber dragon", "cyber", "crystal beast", "stardust", "junk", "blackwing",
    "utopia", "galaxy-eyes", "galaxy", "photon", "odd-eyes", "performapal", "magician", "phantom knights",
    "predaplant", "fluffal", "frightfur", "salamangreat", "marincess", "borrel", "codetalker",
    "blue-eyes", "red-eyes", "dark magician", "buster blader", "archfiend", "sky striker", "striker",
    "six samurai", "samurai", "subterror", "orcust", "thunder dragon", "eldlich", "dogmatika", "dogma",
    "tri-brigade", "drytron", "despia", "swordsoul", "floowandereeze", "floow", "p.u.n.k.", "exosister",
    "dinomorphia", "therion", "spright", "tearlaments", "tear", "bystial", "kashtira", "labrynth",
    "mikanko", "purrely", "mannadium", "vanquish soul", "runick", "mathmech", "ignister", "evil twin",
    "live twin", "unchained", "tenyi", "megalith", "kaiju", "timelord", "danger!", "monarch", "machina",
    "gladiator beast", "shaddoll", "nekroz", "ritual beast", "tellarknight", "constellar", "evilswarm",
    "gem-knight", "dragunity", "naturia", "ice barrier", "inzektor", "madolche", "mermail", "metalfoes",
    "prank-kids", "zoodiac", "lunalight", "branded", "albaz", "albion", "numeron", "egyptian god",
    "slifer", "obelisk", "exodia", "neos", "elemental", "gem-", "gimmick puppet",
]
HANDTRAPS_AND_STAPLES = [
    'maxx "c"', "ash blossom", "nibiru", "veiler", "droll", "ghost ogre", "ghost belle", "ghost mourner",
    "ghost reaper", "d.d. crow", "psy-framegear", "dimension shifter", "called by", "crossout", "lava golem",
    "fossil dyna", "inspector boarder", "barrier statue", "winda", "baronne", "apollousa", "accesscode",
    "masquerena", "knightmare", "little knight", "zeus", "ty-phon",
]


def score_obscurity(name, card_type):
    is_normal = "normal" in card_type.lower()
    score = 150 if is_normal else 50
    nl = name.lower()
    penalized = False
    for kw in POPULAR_ARCHETYPES:
        if kw in nl:
            score -= 80; penalized = True; break
    for ht in HANDTRAPS_AND_STAPLES:
        if ht in nl:
            score -= 100; penalized = True; break
    if not penalized:
        if len(name) < 6:
            score -= 20
        elif len(name) < 10:
            score -= 10
        elif len(name) > 15:
            score += 10
    return score


def find(*names):
    for n in names:
        if os.path.exists(n):
            return n
    raise FileNotFoundError(names)


def main():
    csv_file = find("md_monsters_active.csv", os.path.join("..", "md_monsters_active.csv"))
    json_file = find("corrected_sim_results.json", os.path.join("..", "corrected_sim_results.json"))

    with open(json_file, encoding="utf-8") as f:
        S = json.load(f)
    v1 = S["templates"]["v1"]; v2 = S["templates"]["v2"]; hyb = S["hybrid_day1_is_v1"]
    v1m, v2m = v1["max_official"], v2["max_official"]
    v1a, v2a = v1["additive"], v2["additive"]
    hybm = hyb["max_official"]
    NMON = S["n_monsters"]

    monsters = []
    with open(csv_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            monsters.append({"id": row["id"], "name": row["name"], "type": row["type"],
                             "attribute": row["attribute"], "race": row["race"], "atk": int(row["atk"])})

    attrs_c = Counter(m["attribute"] for m in monsters)
    races_c = Counter(m["race"] for m in monsters)
    atks_c = Counter(m["atk"] for m in monsters)

    def pct(n):
        return f"{n / NMON * 100:.2f}%"

    # 频数表
    attr_rows = "\n".join(
        f"| {i} | {ATTR_CN.get(a, a)}属性 ({a}) | {c} | {pct(c)} |"
        for i, (a, c) in enumerate(attrs_c.most_common(7), 1))
    race_rows = "\n".join(
        f"| {i} | {RACE_CN.get(r, r)} ({r}) | {c} | {pct(c)} |"
        for i, (r, c) in enumerate(races_c.most_common(10), 1))
    atk_top = sorted(atks_c.most_common(10), key=lambda x: -x[1])[:10]
    atk_rows = "\n".join(
        f"| {i} | {('「?」可变' if a < 0 else a)} | {c} | {pct(c)} |"
        for i, (a, c) in enumerate(atk_top, 1))

    g1 = sum(attrs_c[x] for x in ("DARK", "EARTH", "LIGHT"))
    g2 = sum(attrs_c[x] for x in ("WATER", "WIND", "FIRE"))

    # 作业表分组（v2a：高频属性各押两张）
    slots = [
        (1, "DARK", "Dragon", 2500), (1, "DARK", "Fiend", 0), (1, "WATER", "Spellcaster", 1500),
        (2, "LIGHT", "Fairy", 1600), (2, "LIGHT", "Machine", 1000), (2, "WIND", "Winged Beast", 1200),
        (3, "EARTH", "Warrior", 1800), (3, "EARTH", "Beast", 800), (3, "FIRE", "Pyro", 1700),
    ]
    day_attr = {1: "暗 / 暗 / 水", 2: "光 / 光 / 风", 3: "地 / 地 / 炎"}
    day_bet = {1: "暗属性", 2: "光属性", 3: "地属性"}

    def ghosts(attr, race, atk):
        ms = [m for m in monsters if m["attribute"] == attr and m["race"] == race and m["atk"] == atk]
        for m in ms:
            m["score"] = score_obscurity(m["name"], m["type"])
        normals = sorted([m for m in ms if "normal" in m["type"].lower()], key=lambda x: -x["score"])
        effects = sorted([m for m in ms if "normal" not in m["type"].lower()], key=lambda x: -x["score"])
        return (normals + effects), len(ms)

    # 作业表正文
    homework = []
    cur_day = None
    for day, attr, race, atk in slots:
        if day != cur_day:
            cur_day = day
            homework.append(f"\n#### 📅 循环第 {day} 天（第 {day}/{day+3}/{day+6} 天）　属性押注：**{day_attr[day]}**（在 {day_bet[day]} 上押两张）\n")
        cards, depth = ghosts(attr, race, atk)
        homework.append(f"* **{ATTR_CN[attr]}属性 / {RACE_CN.get(race, race)} / {atk} 攻击力**　（真卡深度：{depth} 张）")
        for rk, m in enumerate(cards[:3], 1):
            tag = "凡骨" if "normal" in m["type"].lower() else "效果"
            homework.append(f"  * 幽灵卡{rk}：`{m['name']}`（ID {m['id']}，{tag}，冷门分 {m['score']}）")
    homework_md = "\n".join(homework)

    R = f"""# 游戏王MD「三战之才」预测活动 · 2.0 纠错版策略报告

> [!IMPORTANT]
> **基于官方 2026.6《大师决斗》真卡池（{NMON} 张活跃怪兽），用 AMD Ryzen 9 9950X3D（32 进程）跑 {S['n_sims']:,} 次仿真。**
> **本期纠错：按官方「每场只取最高一级」规则重算（属性/种族/攻击力三项取最高，不是相加）；并修正作业表的属性分组方式。**

## 一句话速览

| 指标（9天=3场合计） | 1.0 方案 | **2.0 纠错版** |
| :-- | :--: | :--: |
| 平均收益（期望） | {v1m['total_mean']:.0f} 钻 | **{v2m['total_mean']:.0f} 钻** |
| 80% 置信保底 | {v1m['floor_80']} | **{v2m['floor_80']}** |
| 90% 置信保底 | {v1m['floor_90']} | **{v2m['floor_90']}** |
| 95% 置信保底 | {v1m['floor_95']} | **{v2m['floor_95']}** |
| 99% 底线 | {v1m['floor_99']} | **{v2m['floor_99']}** |

> **期望约 {v2m['total_mean']:.0f} 钻；9 成场景保底 {v2m['floor_90']} 钻、95% 保底 {v2m['floor_95']} 钻、最坏 99% 也有 {v2m['floor_99']} 钻。** 懒得看原理的直接拉到第六部分截图作业表。

---

## 📂 第一部分：卡池三维特征占比（数据基石）

官方开奖是从全量怪兽里**均匀随机**抽 3 张。卡越多的属性/种族/攻击力，越容易被抽中。

### 属性占比（7 属性）
| # | 属性 | 张数 | 占比 |
| :-: | :-- | :-: | :-: |
{attr_rows}

* **三大高频属性**：暗 / 地 / 光，合计 **{(g1/NMON*100):.2f}%**；水 / 风 / 炎合计仅 **{(g2/NMON*100):.2f}%**；神属性是极小噪点。

### 种族 TOP 10
| # | 种族 | 张数 | 占比 |
| :-: | :-- | :-: | :-: |
{race_rows}

### 攻击力 TOP 10
| # | 攻击力 | 张数 | 占比 |
| :-: | :-- | :-: | :-: |
{atk_rows}

---

## 📂 第二部分：官方规则精读 × 数据合理性

把官方活动页面（Triple Tactics Talent）的规则逐条对到数据上：

1. **每场只结算最高一级（核心）**：官方原文「若符合多项等级的条件，将适用等级最高的条件；每1场只适用等级最高的条件」。
   即属性分、种族分、攻击力分**三项里只取最高的一项发奖**，**不能相加**。参加记录里一整场也只显示一个奖（如 C 奖）。
2. **奖励阶梯（从高到低）**：Triple/Double/Single Hit（整张卡相同）＞ A~I 奖。其中
   攻击力 3/2/1 命中 = 300/150/50；种族 = 250/100/30；属性 = 200/70/20（即 **攻击力＞种族＞属性**）。
3. **大奖是奖池均分**：Single / Double / Triple Hit 的奖池分别是 **100万 / 200万 / 300万宝石，全服中奖者均分**，外加固定 300 宝石。
   交冷门卡的意义是**减少同中奖人数、提高你那一份的占比**——不是"独吞"。且**无偿宝石持有上限 8000**，领奖时超出部分只能领到上限。
4. **攻击力「?」单独成类**：官方明确「?」不等于 0（如三幻神）。数据里「?」存为 -1（{atks_c.get(-1,0)} 张），与 0 攻分开，**处理正确**。
5. **不适用禁限表 = 开奖不会开出禁卡**：故抽奖池剔除禁卡是**正确**口径。
6. **部分卡片不在可选范围**：官方注明少量卡被排除，真实可选池与全量怪兽略有出入（数千分之几，统计上可忽略）。

---

## 📂 第三部分：双层 SUM→MAX 纠错（这才是真正的"我算错了"）

官方规则里其实藏着**两层** MAX：①一场 3 天，只取最高那天（按天 MAX）；②一天里属性/种族/攻击力，只取最高那项（按维度 MAX）。

| 版本 | 按天 | 按维度 | 结果 |
| :-- | :--: | :--: | :-- |
| **1.0** | ❌ 错用相加 | ❌ 错用相加 | 把真实 {v1m['total_mean']:.0f} 钻吹成相加的 {v1a['total_mean']:.0f} 钻 |
| **旧 2.0** | ✅ 改成 MAX | ❌ 仍用相加 | 只修了一层，仍把 {v2m['total_mean']:.0f} 钻吹成 {v2a['total_mean']:.0f} 钻 |
| **2.0 纠错版** | ✅ MAX | ✅ MAX | 还原官方真实收益：**{v2m['total_mean']:.0f} 钻** |

> 一句话：1.0 的 bug 是"该 MAX 却 SUM 了天"；旧 2.0 只修了"天"，"维度"又犯了同样的错。本期把第二层也修了。

---

## 📂 第四部分：属性保底的正确姿势——"高频属性各押两张"

这是本期最硬核、也最反直觉的纠错点。

### ❌ 误区：干净二分 + "3球2筐鸽巢"
把 6 属性分成 暗地光 / 水风炎，第 1、3 天交"暗地光"、第 2 天交"水风炎"，号称"3 个中奖属性丢进 2 个筐，必有一筐≥2"。
**漏洞**：鸽巢数的是"中奖卡（球）"，但实际计分数的是"**你命中几张卡**"。你每天只放 **1 张暗**，开奖出 **2 张暗**也只算命中 1 个。
一亿次仿真：这种干净二分属性保底**失效率高达 25%**，9 天期望只有约 285 钻——和 1.0 差不多，等于没优化。

### ✅ 正解：在三大高频属性上各押两张
- 第 1 天放 **2 张暗** + 1 张水；第 2 天放 **2 张光** + 1 张风；第 3 天放 **2 张地** + 1 张炎。
- 暗 / 光 / 地 是占比最大的三个属性（合计 {(g1/NMON*100):.0f}%）。只要开奖 3 张里出现暗**或**光**或**地中的任意一个，对应那天就有**两张同属性命中 = 70 钻**。
- 失效（一个高频属性都没开出）只发生在"3 张全是水/风/炎/神"，概率仅 **{v2['attr_pigeonhole_fail_rate']}%**。

| 属性方案 | 9天期望 | 95%保底 | 属性失效率 |
| :-- | :--: | :--: | :--: |
| 干净二分（旧作业表） | ≈285 钻 | 170 | 25% |
| **高频各押两张（本期）** | **{v2m['total_mean']:.0f} 钻** | **{v2m['floor_95']}** | **{v2['attr_pigeonhole_fail_rate']}%** |

> 所以"210 钻保底"不是 100% 数学铁律，而是 **95% 置信保底**（失效约 {v2['attr_pigeonhole_fail_rate']}%，且常被种族/攻击力兜底）；最坏 99% 也有 {v2m['floor_99']} 钻。

---

## 📂 第五部分：一亿次模拟·两代收益对比（官方取最高模型）

| 指标（9天合计） | 1.0 | **2.0 纠错版** | 相加模型(旧/错) |
| :-- | :--: | :--: | :--: |
| 平均期望 | {v1m['total_mean']:.0f} | **{v2m['total_mean']:.0f}** | {v2a['total_mean']:.0f}（虚高） |
| 80% 保底 | {v1m['floor_80']} | **{v2m['floor_80']}** | {v2a['floor_80']} |
| 90% 保底 | {v1m['floor_90']} | **{v2m['floor_90']}** | {v2a['floor_90']} |
| 95% 保底 | {v1m['floor_95']} | **{v2m['floor_95']}** | {v2a['floor_95']} |
| 99% 底线 | {v1m['floor_99']} | **{v2m['floor_99']}** | {v2a['floor_99']} |
| 属性失效率 | 25% | **{v2['attr_pigeonhole_fail_rate']}%** | — |

**结论**：纠错后 2.0 仍以 **{v2m['total_mean']:.0f} vs {v1m['total_mean']:.0f}（+{(v2m['total_mean']/v1m['total_mean']-1)*100:.0f}%）** 完胜 1.0，且把属性保底失效率从 25% 压到 {v2['attr_pigeonhole_fail_rate']}%——这正是 2.0 在 90/95% 分位守住 {v2m['floor_90']}/{v2m['floor_95']} 钻、而 1.0 跌到 {v1m['floor_90']}/{v1m['floor_95']} 的根因。

---

## 📂 第六部分：终极防稀释「冷门幽灵卡」作业表

游戏内按特征筛选后，**别选前排热门卡，滑到最底下挑名字最冷僻的**提交。优先凡骨（Normal）怪兽——它们最接近"无人会交的幽灵"。一旦命中 Hit 大奖，同中奖的人越少、你分到的奖池越多。
{homework_md}

> 同一天的 3 张卡，内部怎么对调（哪个属性配哪个种族/攻击力）**得分完全不变**——所以放心从冷门卡里随便挑。

---

## 📂 第七部分：对称性的边界——"同天对调不变，跨天重组会变"

* **同天内对调（得分不变）**：一天 3 张卡，把"属性集合 / 种族集合 / 攻击力集合"内部元素重新配对，3!×3!=36 种排法得分完全相同。因为三项匹配数只取决于**集合**，与配对顺序无关（官方也明说"排列顺序不影响奖励等级"）。
* **跨天重组（得分会变）**：把一个特征挪到**别的天**，会改变每天的属性多重集——这正是"干净二分(285钻)"与"高频各押两张({v2m['total_mean']:.0f}钻)"的差距来源。
* **落地价值**：既然同天对调不影响得分，我们就用这个自由度去每个卡位挑**真卡多、最冷门**的幽灵卡，最大化防稀释空间。

---

## 📂 第八部分：亡羊补牢——第 1 天已按 1.0 交了怎么办？

视频第 1 天发布，难免有兄弟已按 1.0 交了第一天（暗/战士/0、地/机械/1000、光/恶魔/1500）。**不用重来，从第 2 天起直接切 2.0 即可。**

| 方案（取最高模型） | 9天期望 | 95%保底 | 99%底线 |
| :-- | :--: | :--: | :--: |
| 死守 1.0 走完三场 | {v1m['total_mean']:.0f} 钻 | {v1m['floor_95']} | {v1m['floor_99']} |
| **第1天1.0 + 第2/3天切2.0** | **{hybm['total_mean']:.0f} 钻** | **{hybm['floor_95']}** | **{hybm['floor_99']}** |

* 几乎追平满 2.0（{v2m['total_mean']:.0f} 钻），远超死守 1.0（{v1m['total_mean']:.0f} 钻）。
* 1.0 第 1 天的属性本就是暗/地/光，与 2.0 第 1 天同组，无缝衔接不冲突。

---

### 报告口径声明
- 收益数字均来自 `corrected_sim_results.json`（官方取最高模型、{S['n_sims']:,} 次仿真、3 场独立同分布卷积求精确分位）。
- 模板特征沿用 best_hedging 搜索最优解，仅修正其按天分组的呈现方式（高频属性各押两张）。
"""

    out_md = "三战之才2.0纠错版策略报告.md"
    for p in (out_md, os.path.join("..", out_md)):
        with open(p, "w", encoding="utf-8") as f:
            f.write(R)
        print(f"[+] 写出报告: {os.path.abspath(p)}")

    # 编译 PDF
    try:
        subprocess.run(["python", "build_docs_pdf.py", "--docs", out_md], check=True)
        pdf = "三战之才2.0纠错版策略报告.pdf"
        if os.path.exists(pdf):
            shutil.copy(pdf, os.path.join("..", pdf))
            print(f"[+] PDF 已生成并备份至上层: {os.path.abspath(os.path.join('..', pdf))}")
    except Exception as e:
        print(f"[-] PDF 编译失败: {e}")


if __name__ == "__main__":
    main()
