# -*- coding: utf-8 -*-
"""
Master Duel Card Data Fetcher & Cleaner
=======================================
Step 1: Fetch cards from YGOPRODeck API, clean monsters, filter bans, and export to CSV (including type field).
"""
import os
import csv
import requests

def main():
    api_url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
    params = {
        "format": "Master Duel"
    }

    print("[+] 正在从 YGOPRODeck API 拉取最新的 Master Duel 卡池数据...")
    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
    except Exception as e:
        print(f"[-] 接口调用失败: {e}")
        return

    cards = raw_data.get("data", [])
    print(f"[+] 成功拉取到 {len(cards)} 张原始卡牌记录。")

    cleaned_monsters = []
    seen_ids = set()

    for card in cards:
        card_id = card.get("id")
        if not card_id or card_id in seen_ids:
            continue

        # 1. 只保留怪兽卡：type 包含 'Monster'，且不包含 'Spell' 或 'Trap'
        card_type = str(card.get("type", ""))
        card_type_lower = card_type.lower()
        if "monster" not in card_type_lower or "spell" in card_type_lower or "trap" in card_type_lower:
            continue

        # 2. 检查禁限卡状态：如果 banlist_info 中的 ban_master 值为 'Banned'，则剔除
        banlist_info = card.get("banlist_info")
        if banlist_info and isinstance(banlist_info, dict):
            ban_master = banlist_info.get("ban_master")
            if ban_master == "Banned":
                continue

        # 3. 字段提取与清洗
        name = card.get("name", "Unknown")
        attribute = str(card.get("attribute", "NONE")).upper()
        race = card.get("race", "NONE")
        atk = card.get("atk", -1)

        cleaned_monsters.append({
            "id": card_id,
            "name": name,
            "type": card_type,  # 导出卡片类型，用于后续筛选凡骨怪兽
            "attribute": attribute,
            "race": race,
            "atk": atk
        })
        seen_ids.add(card_id)

    print(f"[+] 清洗与去重完成。符合条件的活跃怪兽卡共计: {len(cleaned_monsters)} 张。")

    # 导出到本地 CSV 文件
    csv_file = "md_monsters_active.csv"
    
    paths_to_write = [csv_file, os.path.join("..", csv_file)]
    
    for path in paths_to_write:
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "type", "attribute", "race", "atk"])
                writer.writeheader()
                writer.writerows(cleaned_monsters)
            print(f"[+] 数据成功导出至: {os.path.abspath(path)}")
        except Exception as e:
            print(f"[-] 导出至 {path} 失败: {e}")

if __name__ == "__main__":
    main()
