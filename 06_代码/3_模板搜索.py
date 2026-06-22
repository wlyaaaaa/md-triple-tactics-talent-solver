# -*- coding: utf-8 -*-
"""
Multi-Day Hedging Template Search (Randomized Greedy Search)
============================================================
Step 3: Fast randomized greedy search to find optimal 3-day 9-card allocation templates,
satisfying G1/G2 attribute partition, unique races, and unique ATKs.
"""
import os
import csv
import json
import random

def load_active_nodes(file_path):
    nodes = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append({
                "attribute": row["attribute"],
                "race": row["race"],
                "atk": int(row["atk"]),
                "card_count": int(row["card_count"]),
                "sample_cards": row["sample_cards"]
            })
    return nodes

def main():
    csv_file = "active_feature_nodes.csv"
    if not os.path.exists(csv_file):
        csv_file = os.path.join("..", csv_file)
        if not os.path.exists(csv_file):
            print("[-] 错误: 找不到活性特征节点文件 active_feature_nodes.csv，请确认 Step 2 是否成功执行。")
            return

    print(f"[+] 正在加载活性特征节点: {os.path.abspath(csv_file)} ...")
    nodes = load_active_nodes(csv_file)
    print(f"[+] 成功加载了 {len(nodes)} 个活性特征节点。")

    # 提取唯一的种族和攻击力列表
    all_races = list(set(n["race"] for n in nodes))
    all_atks = list(set(n["atk"] for n in nodes))

    # 目标属性模板（严格三日无交集对冲）：
    # Day 1: DARK, DARK, WATER   (覆盖 DARK, WATER)
    # Day 2: LIGHT, LIGHT, WIND   (覆盖 LIGHT, WIND)
    # Day 3: EARTH, EARTH, FIRE   (覆盖 EARTH, FIRE)
    # 物理覆盖全部6个属性，且每天的属性集互不重合，消除天级收益正相关性
    attributes_template = [
        "DARK", "DARK", "WATER",  # Day 1
        "LIGHT", "LIGHT", "WIND",  # Day 2
        "EARTH", "EARTH", "FIRE"   # Day 3
    ]

    print("[+] 启动启发式随机贪心搜索 (Randomized Greedy Search)...")
    
    unique_templates = {}
    iterations = 50000
    
    for _ in range(iterations):
        unused_races = set(all_races)
        unused_atks = set(all_atks)
        
        # 记录 9 个卡位的最终选择
        template = [None] * 9
        
        # 随机分配位置的填充顺序（变量排序启发式，能极大地增加可行解多样性）
        order = list(range(9))
        random.shuffle(order)
        
        success = True
        for pos in order:
            attr = attributes_template[pos]
            
            # 过滤出符合当前卡位属性、且 race/atk 未被占用的活性节点
            candidates = [
                n for n in nodes
                if n["attribute"] == attr and n["race"] in unused_races and n["atk"] in unused_atks
            ]
            
            if not candidates:
                success = False
                break
                
            # 贪心选择：按卡池数降序排列，随机从前几名中挑选一个（引入噪声防局部最优）
            candidates.sort(key=lambda x: x["card_count"], reverse=True)
            # 90% 概率选第一名（纯贪心），10% 概率选第二/三名（探索）
            select_idx = 0
            if len(candidates) > 1 and random.random() < 0.1:
                select_idx = random.randint(0, min(2, len(candidates) - 1))
                
            chosen = candidates[select_idx]
            
            template[pos] = {
                "day": (pos // 3) + 1,
                "card_idx": (pos % 3) + 1,
                "attribute": chosen["attribute"],
                "race": chosen["race"],
                "atk": chosen["atk"],
                "card_count": chosen["card_count"],
                "sample_cards": chosen["sample_cards"]
            }
            
            unused_races.remove(chosen["race"])
            unused_atks.remove(chosen["atk"])
            
        if success:
            total_weight = sum(c["card_count"] for c in template)
            # 用特征元组序列作为唯一键，防止输出重复模板
            t_key = tuple((c["attribute"], c["race"], c["atk"]) for c in template)
            if t_key not in unique_templates or total_weight > unique_templates[t_key]["weight"]:
                unique_templates[t_key] = {
                    "weight": total_weight,
                    "template": template
                }

    # 排序并筛选出前 5 个最强的不同模板
    sorted_templates = sorted(unique_templates.values(), key=lambda x: x["weight"], reverse=True)
    
    print(f"[+] 搜索完成。在 {iterations} 次迭代中筛选出 {len(sorted_templates)} 种不重复的可行模板。")

    output_templates = []
    for rank, item in enumerate(sorted_templates[:5], 1):
        weight = item["weight"]
        template = item["template"]
        print(f"\n==================================================")
        print(f" [*] 候选模板 #{rank} (联合物理卡池基数: {weight} 张怪兽卡)")
        print(f"==================================================")
        
        day_info = {1: [], 2: [], 3: []}
        for card in template:
            day_info[card["day"]].append(card)
            
        for d in [1, 2, 3]:
            print(f"  [*] 第 {d} 天：")
            for c in day_info[d]:
                print(f"    - 卡位 {c['card_idx']}: 【{c['attribute']:<5} / {c['race']:<15} / {c['atk']:<4}】 (卡池深度: {c['card_count']:>3} 张)")
                
        output_templates.append({
            "rank": rank,
            "total_card_count": weight,
            "template": template
        })

    # 导出为 JSON 供第四步使用
    json_file = "candidate_templates.json"
    paths_to_write = [json_file, os.path.join("..", json_file)]
    
    for path in paths_to_write:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(output_templates, f, indent=2, ensure_ascii=False)
            print(f"\n[+] 候选分配模板已成功导出至: {os.path.abspath(path)}")
        except Exception as e:
            print(f"[-] 导出至 {path} 失败: {e}")

if __name__ == "__main__":
    main()
