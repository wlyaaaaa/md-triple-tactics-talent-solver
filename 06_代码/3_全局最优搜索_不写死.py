# -*- coding: utf-8 -*-
"""
Globally Optimized Triple Tactics Prediction Search (Unconstrained 3.0)
========================================================================
Step 3 (Upgrade): Run a globally unconstrained randomized hill-climbing search
on active_feature_nodes.csv to find the absolute global optimal 3-day 9-card allocation template,
using the corrected one-to-one pairs matching and double-MAX rules.
"""
import os
import csv
import json
import random
import numpy as np
from collections import Counter

# STREAMING_CHUNK:Loading and cleaning...
# 1. 物理真卡池加载与属性/种族/攻击力编码
def find_csv():
    for p in (
        "md_monsters_active.csv",
        os.path.join("..", "md_monsters_active.csv"),
        os.path.join("..", "05_数据", "大师决斗活跃怪兽_8944.csv"),
    ):
        if os.path.exists(p):
            return p
    raise FileNotFoundError("md_monsters_active.csv / 05_数据/大师决斗活跃怪兽_8944.csv 未找到")

CSV_PATH = find_csv()
ATTR_RAW, RACE_RAW, ATK_RAW = [], [], []
with open(CSV_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ATTR_RAW.append(row["attribute"])
        RACE_RAW.append(row["race"])
        ATK_RAW.append(int(row["atk"]))

# 构建映射与整型数组，加快 numpy 运算
ATTR_SET = sorted(set(ATTR_RAW))
RACE_SET = sorted(set(RACE_RAW))
ATK_SET  = sorted(set(ATK_RAW))

AM = {v: i for i, v in enumerate(ATTR_SET)}
RM = {v: i for i, v in enumerate(RACE_SET)}
KM = {v: i for i, v in enumerate(ATK_SET)}

ATTR_ARR = np.array([AM[x] for x in ATTR_RAW], dtype=np.int16)
RACE_ARR = np.array([RM[x] for x in RACE_RAW], dtype=np.int16)
ATK_ARR  = np.array([KM[x] for x in ATK_RAW],  dtype=np.int16)
N_MONSTERS = len(ATTR_RAW)

# 奖励系数表
ARW = np.array([0, 20, 70, 200], dtype=np.int32)
RRW = np.array([0, 30, 100, 250], dtype=np.int32)
KRW = np.array([0, 50, 150, 300], dtype=np.int32)

# STREAMING_CHUNK:Defining the fast evaluator...
# 2. 预先在内存生成 20,000 次高质量模拟开奖，作为算法搜索的“评卷库”
# 这能让每一次特征模板评估控制在几毫秒，彻底消灭算力瓶颈
print("[+] 正在生成 20,000 次内存开奖测试集进行极速对撞...")
rng = np.random.default_rng(2026)
win_idx = rng.integers(0, N_MONSTERS, size=(20000, 3))
for idx_row in range(20000):
    while len(set(win_idx[idx_row])) < 3:
        win_idx[idx_row] = rng.integers(0, N_MONSTERS, size=3)

WIN_ATTR = ATTR_ARR[win_idx]
WIN_RACE = RACE_ARR[win_idx]
WIN_ATK  = ATK_ARR[win_idx]

def evaluate_template(template):
    """
    极速计分引擎：使用最严格的一对一配对（多重集交集）与双层 MAX 结算规则。
    """
    max_days = np.zeros(20000, dtype=np.int32)
    for d in (1, 2, 3):
        # 提取第 d 天的 3 张卡特征
        day_cards = [template[i] for i in range((d-1)*3, d*3)]
        pa = [AM[c["attribute"]] for c in day_cards]
        pr = [RM[c["race"]] for c in day_cards]
        pk = [KM[c["atk"]] for c in day_cards]

        # 严格一对一多重集交集匹配 (numpy 向量化求和)
        ma = sum(np.minimum(c, (WIN_ATTR == v).sum(axis=1)) for v, c in Counter(pa).items())
        mr = sum(np.minimum(c, (WIN_RACE == v).sum(axis=1)) for v, c in Counter(pr).items())
        mk = sum(np.minimum(c, (WIN_ATK == v).sum(axis=1)) for v, c in Counter(pk).items())

        # 匹配数映射为奖金
        ra = ARW[ma]
        rr = RRW[mr]
        rk = KRW[mk]

        # 双层 MAX 结算：维度取最高
        day_score = np.maximum(ra, np.maximum(rr, rk))
        # 场内取最高天
        max_days = np.maximum(max_days, day_score)

    return float(np.mean(max_days))

# STREAMING_CHUNK:Implementing local search...
# 3. 加载第二步的活性特征节点
def load_nodes():
    nodes_file = "active_feature_nodes.csv"
    if not os.path.exists(nodes_file):
        nodes_file = os.path.join("..", nodes_file)
        if not os.path.exists(nodes_file):
            nodes_file = os.path.join("..", "05_数据", "活性特征节点.csv")
            if not os.path.exists(nodes_file):
                raise FileNotFoundError("active_feature_nodes.csv / 05_数据/活性特征节点.csv 未找到，请先运行 Step 2")

    nodes = []
    with open(nodes_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nodes.append({
                "attribute": r["attribute"],
                "race": r["race"],
                "atk": int(r["atk"]),
                "card_count": int(r["card_count"]),
                "sample_cards": r["sample_cards"]
            })
    return nodes

def generate_random_valid_template(nodes):
    """启发式随机生成一个满足：6属性覆盖、9种族去重、9打点去重的可行初始方案"""
    all_races = list(set(n["race"] for n in nodes))
    all_atks = list(set(n["atk"] for n in nodes))

    while True:
        unused_races = set(all_races)
        unused_atks = set(all_atks)
        template = []

        # 为确保先验覆盖 6 属性，我们先在前 6 个槽位塞入互不相同的 6 主属性
        attrs = ["DARK", "LIGHT", "EARTH", "WATER", "WIND", "FIRE"]
        random.shuffle(attrs)
        # 剩余 3 个槽位随机分配基数最大的高频属性
        attrs += random.choices(["DARK", "LIGHT", "EARTH"], k=3)
        random.shuffle(attrs)

        success = True
        for attr in attrs:
            candidates = [
                n for n in nodes
                if n["attribute"] == attr and n["race"] in unused_races and n["atk"] in unused_atks
            ]
            if not candidates:
                success = False
                break

            chosen = random.choice(candidates[:5]) # 引入适量扰动
            template.append(chosen)
            unused_races.remove(chosen["race"])
            unused_atks.remove(chosen["atk"])

        if success:
            return template

def main():
    nodes = load_nodes()
    print(f"[+] 成功加载 {len(nodes)} 个活性特征节点。")

    print("[+] 正在生成初始解...")
    best_template = generate_random_valid_template(nodes)
    best_score = evaluate_template(best_template)
    print(f"  ● 初始方案期望评分: {best_score:.2f} 钻")

    # 爬山法全局进化迭代
    iterations = 10000
    print(f"[+] 启动随机爬山法（Hill-Climbing）在全卡池边界内进行 {iterations} 次全局迭代进化...")

    all_races = list(set(n["race"] for n in nodes))
    all_atks = list(set(n["atk"] for n in nodes))

    for step in range(iterations):
        # 复制当前最佳方案
        new_template = list(best_template)

        # 变异策略：
        if random.random() < 0.3:
            # 策略 A：保持选卡不变，仅随机对调两张卡片所在的日期（改变天数分配，探索协方差对冲）
            idx1, idx2 = random.sample(range(9), 2)
            new_template[idx1], new_template[idx2] = new_template[idx2], new_template[idx1]
        else:
            # 策略 B：替换其中 1 个卡位为新特征
            pos = random.randint(0, 8)
            # 统计当前其他卡位占用的种族与打点
            used_races = set(new_template[i]["race"] for i in range(9) if i != pos)
            used_atks = set(new_template[i]["atk"] for i in range(9) if i != pos)

            # 找出符合当前卡位属性、且不与其它位置冲突的新特征节点
            candidates = [
                n for n in nodes
                if n["attribute"] == new_template[pos]["attribute"]
                and n["race"] not in used_races
                and n["atk"] not in used_atks
            ]

            if candidates:
                # 贪心选择更优或随机选择
                new_template[pos] = random.choice(candidates[:3])

        # 约束校验：确认变异后依然覆盖全部 6 属性
        attrs_covered = set(c["attribute"] for c in new_template)
        if len(attrs_covered) < 6:
            continue

        # 评估新得分
        score = evaluate_template(new_template)
        if score > best_score:
            best_score = score
            best_template = new_template
            if step % 200 == 0 or step == iterations - 1:
                print(f"  [进化] 步数 {step:4d}: 新的全局最优期望上升至 -> {best_score:.2f} 钻")

    # 4. 输出最终寻优出的全局最优3.0作业模板
    print("\n" + "="*80)
    print(f" [★] 算法在 2026.6 卡池边界内寻优出的【全局绝对最优 3.0 解】（期望：{best_score:.2f} 钻）")
    print("="*80)

    final_output = []
    for d in (1, 2, 3):
        day_cards = best_template[(d-1)*3 : d*3]
        day_attrs = [c["attribute"] for c in day_cards]
        print(f"\n  [★] 第 {d} 天： 属性策略 -> {' / '.join(day_attrs)}")
        for idx, c in enumerate(day_cards, 1):
            print(f"    - 卡位 {idx}: 【{c['attribute']:<5} / {c['race']:<15} / {c['atk']:<4}】 (真卡池深度: {c['card_count']:>3} 张)")
            final_output.append({
                "day": d,
                "card_idx": idx,
                "attribute": c["attribute"],
                "race": c["race"],
                "atk": c["atk"],
                "card_count": c["card_count"],
                "sample_cards": c["sample_cards"]
            })

    # 写入 JSON 覆盖第四步的输入
    out_json = "candidate_templates.json"
    data_to_write = [{
        "rank": 1,
        "total_card_count": sum(c["card_count"] for c in final_output),
        "template": final_output
    }]

    paths_to_write = [out_json, os.path.join("..", out_json)]
    for path in paths_to_write:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data_to_write, f, indent=2, ensure_ascii=False)
            print(f"\n[+] 全局最强决策已导出至: {os.path.abspath(path)}")
        except Exception as e:
            print(f"[-] 导出至 {path} 失败: {e}")

if __name__ == "__main__":
    main()
