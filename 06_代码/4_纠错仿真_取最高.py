# -*- coding: utf-8 -*-
"""
三战之才 3.0 自动版 · 一亿次高精度仿真（严格配对纠错）
======================================================
Step 4 (Upgrade): Automatically load the globally optimized 3.0 template from
candidate_templates.json, and run 100M simulations under strict one-to-one pairs
matching and double-MAX rules.
"""
import os
import csv
import json
import numpy as np
import multiprocessing as mp
from collections import Counter

# ---------- 全局：加载真卡池并数字化 ----------
def _find_csv():
    for p in (
        "md_monsters_active.csv",
        os.path.join("..", "md_monsters_active.csv"),
        os.path.join("..", "05_数据", "大师决斗活跃怪兽_8944.csv"),
    ):
        if os.path.exists(p):
            return p
    raise FileNotFoundError("md_monsters_active.csv / 05_数据/大师决斗活跃怪兽_8944.csv 未找到")

_CSV = _find_csv()
_ATTR, _RACE, _ATK = [], [], []
with open(_CSV, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        _ATTR.append(row["attribute"])
        _RACE.append(row["race"])
        _ATK.append(int(row["atk"]))

A = sorted(set(_ATTR)); R = sorted(set(_RACE)); K = sorted(set(_ATK))
AM = {v: i for i, v in enumerate(A)}; RM = {v: i for i, v in enumerate(R)}; KM = {v: i for i, v in enumerate(K)}
ATTR = np.array([AM[x] for x in _ATTR], dtype=np.int16)
RACE = np.array([RM[x] for x in _RACE], dtype=np.int16)
ATK  = np.array([KM[x] for x in _ATK],  dtype=np.int16)
NMON = len(_ATTR)

# 奖励对照表
ARW = np.array([0, 20, 70, 200], dtype=np.int32)
RRW = np.array([0, 30, 100, 250], dtype=np.int32)
KRW = np.array([0, 50, 150, 300], dtype=np.int32)

# ---------- 动态读取第 3 步生成的 3.0 全局最优模板 ----------
def load_templates():
    json_path = "candidate_templates.json"
    if not os.path.exists(json_path):
        json_path = os.path.join("..", json_path)
        if not os.path.exists(json_path):
            json_path = os.path.join("..", "05_数据", "候选模板.json")
            if not os.path.exists(json_path):
                raise FileNotFoundError("candidate_templates.json / 05_数据/候选模板.json 未找到，请先运行 Step 3")

    with open(json_path, encoding="utf-8") as f:
        candidates = json.load(f)

    t3_raw = candidates[0]["template"]

    # 转化为内部计算格式
    t3 = {1: [], 2: [], 3: []}
    for c in t3_raw:
        t3[c["day"]].append((c["attribute"], c["race"], c["atk"]))

    # 经典 1.0对照组
    t1 = {
        1: [("DARK", "Warrior", 0), ("EARTH", "Machine", 1000), ("LIGHT", "Fiend", 1500)],
        2: [("WATER", "Dragon", 1800), ("WIND", "Spellcaster", 2000), ("FIRE", "Fairy", 1600)],
        3: [("LIGHT", "Cyberse", 2500), ("DARK", "Winged Beast", 1200), ("EARTH", "Beast", 3000)],
    }
    return {"v1": t1, "v3": t3}

TEMPLATES = load_templates()

def _encode(t):
    pa = {d: [AM[c[0]] for c in t[d]] for d in t}
    pr = {d: [RM[c[1]] for c in t[d]] for d in t}
    pk = {d: [KM.get(c[2], -99) for c in t[d]] for d in t}
    return pa, pr, pk

ENC = {name: _encode(t) for name, t in TEMPLATES.items()}

# STREAMING_CHUNK:Defining the fast evaluator...
def _round_scores(idx, pa, pr, pk):
    """严格一对一配对计分（np.minimum 限制最大匹配数）"""
    wa = ATTR[idx]; wr = RACE[idx]; wk = ATK[idx]
    max_days = []
    for d in (1, 2, 3):
        # 统计频数并限制多重集交集
        ma = sum(np.minimum(c, (wa == v).sum(axis=1)) for v, c in Counter(pa[d]).items())
        mr = sum(np.minimum(c, (wr == v).sum(axis=1)) for v, c in Counter(pr[d]).items())
        mk = sum(np.minimum(c, (wk == v).sum(axis=1)) for v, c in Counter(pk[d]).items())
        ra = ARW[ma]; rr = RRW[mr]; rk = KRW[mk]
        # 双层 MAX 结算：天数最高，维度最高
        max_days.append(np.maximum(ra, np.maximum(rr, rk)))
    max_r = np.maximum.reduce(max_days)
    return max_r

def worker(args):
    seed, n = args
    rng = np.random.default_rng(seed)
    hist = {name: np.zeros(301, np.int64) for name in ENC}
    sub = 500_000
    done = 0
    while done < n:
        m = min(sub, n - done)
        idx = rng.integers(0, NMON, size=(m, 3))
        while True:
            dup = (idx[:, 0] == idx[:, 1]) | (idx[:, 1] == idx[:, 2]) | (idx[:, 0] == idx[:, 2])
            c = int(dup.sum())
            if c == 0:
                break
            idx[dup] = rng.integers(0, NMON, size=(c, 3))
        for name, (pa, pr, pk) in ENC.items():
            max_r = _round_scores(idx, pa, pr, pk)
            hist[name] += np.bincount(max_r, minlength=301)
        done += m
    return hist

# STREAMING_CHUNK:Implementing local search...
def _stats_from_hist(counts):
    total = counts.sum()
    pmf = counts / total
    vals = np.arange(len(pmf))
    round_mean = float((pmf * vals).sum())

    total_pmf = np.convolve(np.convolve(pmf, pmf), pmf)
    tvals = np.arange(len(total_pmf))
    total_mean = float((total_pmf * tvals).sum())
    cdf = np.cumsum(total_pmf)

    def floor_at(conf):
        q = 1.0 - conf
        i = int(np.searchsorted(cdf, q, side="left"))
        return int(tvals[min(i, len(tvals) - 1)])

    return {
        "round_mean": round(round_mean, 2),
        "total_mean": round(total_mean, 2),
        "floor_80": floor_at(0.80),
        "floor_90": floor_at(0.90),
        "floor_95": floor_at(0.95),
        "floor_99": floor_at(0.99),
        "round_min": int(vals[counts > 0][0]),
        "round_max": int(vals[counts > 0][-1]),
    }

def main():
    TOTAL = 100_000_000
    NPROC = min(mp.cpu_count(), 32)
    per = TOTAL // NPROC
    tasks = [(2026 + i, per) for i in range(NPROC)]
    print(f"[+] 正在加载 candidate_templates.json 作为 3.0 输入源...")
    print(f"[+] 卡池 {NMON} 张；{NPROC} 进程 × {per:,} = {per*NPROC:,} 次开奖仿真（严格配对纠错版）...")

    with mp.Pool(NPROC) as pool:
        parts = pool.map(worker, tasks)

    agg = {name: np.zeros(301, np.int64) for name in ENC}
    for h in parts:
        for name in ENC:
            agg[name] += h[name]

    results = {"n_sims": per * NPROC, "n_monsters": NMON, "templates": {}}
    for name, label in [("v1", "1.0 方案"), ("v3", "3.0 全局最优解")]:
        max_stats = _stats_from_hist(agg[name])
        results["templates"][name] = {"max_official": max_stats}

    print("\n" + "=" * 78)
    print(" 官方『双层MAX+严格配对』纠错模型 一亿次终极仿真结果")
    print("=" * 78)
    for name, label in [("v1", "1.0 方案"), ("v3", "3.0 全局最优解")]:
        x = results["templates"][name]["max_official"]
        print(f"\n【{label}】")
        print(f"  严格配对 9天期望收益: {x['total_mean']:.2f} 钻")
        print(f"  置信保底收益: 80%={x['floor_80']}  90%={x['floor_90']}  95%={x['floor_95']}  99%={x['floor_99']}")
        print(f"  单场区间[min={x['round_min']}, max={x['round_max']}]")

    out = "corrected_sim_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[+] 精确模拟结果已保存至: {os.path.abspath(out)}")

if __name__ == "__main__":
    mp.freeze_support()
    main()
