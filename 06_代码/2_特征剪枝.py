# -*- coding: utf-8 -*-
"""
Heuristic Feature Pruning & Reality Projection
==============================================
Step 2: Filter attributes, extract Top 9 races/ATKs, match with real cards in parallel,
and prune inactive/congested nodes using the Pigeonhole Principle attribute partitioning.
"""
import os
import csv
import multiprocessing
from collections import Counter

# 著名热门卡片黑名单（用于防止选择坍缩在大奖均分稀释严重的节点上）
POPULAR_MONSTERS = {
    "Maxx \"C\"", "Ash Blossom & Joyous Spring", "Effect Veiler",
    "Nibiru, the Primal Being", "Droll & Lock Bird", "Ghost Belle & Haunted Mansion",
    "D.D. Crow", "Psy-Framegear Gamma", "Kuriboh", "Blue-Eyes White Dragon",
    "Dark Magician", "Red-Eyes Black Dragon", "Ghost Mourner & Moonlit Chill",
    "Dimension Shifter", "Ghost Ogre & Snow Rabbit"
}

# 6大主流属性
VALID_ATTRIBUTES = {"LIGHT", "DARK", "EARTH", "WATER", "WIND", "FIRE"}

def count_matching_cards(args):
    """
    工作线程：计算单个特征组合在真实卡池中的卡片数，并检查是否属于拥堵节点
    """
    attr, race, atk, monster_list = args
    matching_cards = []
    
    for m in monster_list:
        if m["attribute"] == attr and m["race"] == race and m["atk"] == atk:
            matching_cards.append(m["name"])
            
    card_count = len(matching_cards)
    
    # 过滤规则：
    # 1. 过滤空集（card_count == 0）
    if card_count == 0:
        return None
        
    # 2. 过滤卡池数极少（<=2）且包含高热度怪兽的组合（防止大奖均分坍缩）
    if card_count <= 2:
        has_popular = any(name in POPULAR_MONSTERS for name in matching_cards)
        if has_popular:
            return None
            
    # 划分属性组，用于第三步的协方差对冲属性严格无交集划分
    # 组 1：高频组 (DARK, EARTH, LIGHT)
    # 组 2：中低频组 (WATER, WIND, FIRE)
    attr_group = "G1" if attr in {"DARK", "EARTH", "LIGHT"} else "G2"
            
    return {
        "attribute": attr,
        "race": race,
        "atk": atk,
        "card_count": card_count,
        "attribute_group": attr_group,
        "sample_cards": ", ".join(matching_cards[:3])  # 保留前3张样例卡展示
    }

def main():
    csv_file = "md_monsters_active.csv"
    if not os.path.exists(csv_file):
        # 尝试从父目录寻找
        csv_file = os.path.join("..", csv_file)
        if not os.path.exists(csv_file):
            print(f"[-] 错误: 找不到输入文件 md_monsters_active.csv，请确认 Step 1 是否执行成功。")
            return

    print(f"[+] 正在加载怪兽卡数据库 {os.path.abspath(csv_file)} ...")
    
    # 说明信息：K社不将限制和禁卡剔除，会有极小误差（约 50 张怪兽）
    print("[!] 注意：由于科乐美官方 API format=Master Duel 接口不主动剔除限制卡与禁止卡，")
    print("[!] 数据库中会保留约 50 张已被禁止的怪兽卡，本系统在后续博弈选卡时会自动规避。")

    monsters = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["atk"] = int(row["atk"])
            monsters.append(row)

    print(f"[+] 成功读取 {len(monsters)} 条怪兽记录。")

    # 1. 属性过滤：仅保留六大主属性，剔除 DIVINE 或空值
    monsters_filtered = [m for m in monsters if m["attribute"] in VALID_ATTRIBUTES]
    print(f"[+] 属性过滤完成，保留六大主属性卡片: {len(monsters_filtered)} 张。")

    # 2. 单维度频数统计：race 种族 & atk 攻击力
    races = [m["race"] for m in monsters_filtered]
    race_counts = Counter(races)
    top_9_races = [item[0] for item in race_counts.most_common(9)]
    print(f"\n[+] 频数排名前 9 的种族：")
    for idx, (r, count) in enumerate(race_counts.most_common(9), 1):
        print(f"  {idx}. {r:<15} : {count} 张 ({count/len(monsters_filtered)*100:.2f}%)")

    # 过滤非整百的攻击力（如 50, 10, -1 等，0属于整百倍数予以保留）
    atks_valid = [m["atk"] for m in monsters_filtered if m["atk"] >= 0 and m["atk"] % 100 == 0]
    atk_counts = Counter(atks_valid)
    top_9_atks = [item[0] for item in atk_counts.most_common(9)]
    print(f"\n[+] 频数排名前 9 的有效攻击力：")
    for idx, (a, count) in enumerate(atk_counts.most_common(9), 1):
        print(f"  {idx}. {a:<15} : {count} 张 ({count/len(monsters_filtered)*100:.2f}%)")

    # 3. 生成 486 个特征交叉组合
    grid = []
    for attr in VALID_ATTRIBUTES:
        for race in top_9_races:
            for atk in top_9_atks:
                grid.append((attr, race, atk))
    print(f"\n[+] 特征空间已生成，共 {len(grid)} 个交叉特征节点。")

    # 4. 多线程 Inner Join 与剪枝（支持32线程硬件加速）
    num_workers = min(multiprocessing.cpu_count(), 32)
    print(f"[+] 检测到系统 CPU 核心，启动 {num_workers} 个并行线程进行交叉真实度投影计算...")
    
    tasks = [(attr, race, atk, monsters_filtered) for attr, race, atk in grid]
    
    with multiprocessing.Pool(num_workers) as pool:
        results = pool.map(count_matching_cards, tasks)

    # 过滤掉被剪枝的空集或拥堵节点
    active_nodes = [r for r in results if r is not None]
    
    # 降序排列
    active_nodes.sort(key=lambda x: x["card_count"], reverse=True)

    print(f"[+] 计算与剪枝完成。真实存在且具足够冷门卡深度的活性节点共计: {len(active_nodes)} 个。")

    # 5. 输出活性特征节点 CSV
    out_file = "active_feature_nodes.csv"
    paths_to_write = [out_file, os.path.join("..", out_file)]
    
    for path in paths_to_write:
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["attribute", "race", "atk", "card_count", "attribute_group", "sample_cards"])
                writer.writeheader()
                writer.writerows(active_nodes)
            print(f"[+] 活性特征节点已导出至: {os.path.abspath(path)}")
        except Exception as e:
            print(f"[-] 导出至 {path} 失败: {e}")

    # 6. 新灵感：输出关于“属性无交集划分”的对冲指导报告
    print("\n" + "="*80)
    print(" [*] 统计学与博弈论对冲指导报告（鸽巢原理底线保障）")
    print("="*80)
    print("  ● 根据鸽巢原理（Pigeonhole Principle）：")
    print("    如果我们将 6 主属性严格划分在单场的前两天提交（天1选高频G1，天2选低频G2），")
    print("    系统开出的 3 张中奖卡片中，必然有一天的属性匹配数 >= 2。")
    print("    这可以在数学上 100% 锁定该场属性预测保底为 70 钻（或全中的 200 钻），对冲单场 0 钻风险。")
    print("  ● 活性特征节点已根据 G1 (DARK, EARTH, LIGHT) 和 G2 (WATER, WIND, FIRE) 进行了属性分组。")
    print("  ● 极值优化任务（第三步）将直接读取该活性特征矩阵进行天级对冲与仿真搜寻。")
    print("="*80 + "\n")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
