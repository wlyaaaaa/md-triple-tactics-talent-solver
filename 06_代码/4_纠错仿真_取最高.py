# -*- coding: utf-8 -*-
"""
三战之才 2.0 纠错版 · 官方"取最高一级"模型 一亿次仿真
=====================================================
核心修正：官方规则「每1场只适用等级最高的条件」——属性/种族/攻击力三项是
          【取最高一项】发奖，而非相加。本脚本把日得分从 (r_a + r_r + r_k)
          改为 max(r_a, r_r, r_k)，并同时保留相加模型用于对照。

结构性事实：每场=3天×3张=9张预测卡，系统每场开3张中奖卡，取该场最高一级；
            9天共3场，三场相互独立同分布(i.i.d.)，故9天总分 = 3个独立场分之和。
            利用这一点，单场得分用直方图统计后，对直方图做3次自卷积即得
            9天总分的精确分布 → 期望与各分位保底均为精确解。

硬件：AMD Ryzen 9 9950X3D，32 进程并发。
输出：corrected_sim_results.json （供报告生成器引用，杜绝写死数字）
"""
import os, csv, json
import numpy as np
import multiprocessing as mp

# ---------- 全局：加载真卡池并数字化（spawn 下每个子进程 import 时各自加载）----------
def _find_csv():
    for p in ("md_monsters_active.csv", os.path.join("..", "md_monsters_active.csv")):
        if os.path.exists(p):
            return p
    raise FileNotFoundError("md_monsters_active.csv 未找到")

_CSV = _find_csv()
_ATTR, _RACE, _ATK = [], [], []
with open(_CSV, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        _ATTR.append(row["attribute"]); _RACE.append(row["race"]); _ATK.append(int(row["atk"]))

A = sorted(set(_ATTR)); R = sorted(set(_RACE)); K = sorted(set(_ATK))
AM = {v: i for i, v in enumerate(A)}; RM = {v: i for i, v in enumerate(R)}; KM = {v: i for i, v in enumerate(K)}
ATTR = np.array([AM[x] for x in _ATTR], dtype=np.int16)
RACE = np.array([RM[x] for x in _RACE], dtype=np.int16)
ATK  = np.array([KM[x] for x in _ATK],  dtype=np.int16)
NMON = len(_ATTR)

# 奖励对照表（官方截图 130-133）：1/2/3 命中
ARW = np.array([0, 20, 70, 200], dtype=np.int32)   # 属性 I/F/C 奖
RRW = np.array([0, 30, 100, 250], dtype=np.int32)  # 种族 H/E/B 奖
KRW = np.array([0, 50, 150, 300], dtype=np.int32)  # 攻击力 G/D/A 奖

# 两套模板
TEMPLATES = {
    "v1": {  # 1.0 版（来自 1.0版本最终最优解 图）
        1: [("DARK", "Warrior", 0), ("EARTH", "Machine", 1000), ("LIGHT", "Fiend", 1500)],
        2: [("WATER", "Dragon", 1800), ("WIND", "Spellcaster", 2000), ("FIRE", "Fairy", 1600)],
        3: [("LIGHT", "Cyberse", 2500), ("DARK", "Winged Beast", 1200), ("EARTH", "Beast", 3000)],
    },
    "v2": {  # 2.0 最优（best_hedging）：三大高频属性各押两张 D1=暗暗水 / D2=光光风 / D3=地地炎
        1: [("DARK", "Dragon", 2500), ("DARK", "Fiend", 0), ("WATER", "Spellcaster", 1500)],
        2: [("LIGHT", "Fairy", 1600), ("LIGHT", "Machine", 1000), ("WIND", "Winged Beast", 1200)],
        3: [("EARTH", "Warrior", 1800), ("EARTH", "Beast", 800), ("FIRE", "Pyro", 1700)],
    },
    "hyb_r1": {  # 亡羊补牢·第1场：Day1沿用1.0已交，Day2/3切2.0
        1: [("DARK", "Warrior", 0), ("EARTH", "Machine", 1000), ("LIGHT", "Fiend", 1500)],
        2: [("LIGHT", "Fairy", 1600), ("LIGHT", "Machine", 1000), ("WIND", "Winged Beast", 1200)],
        3: [("EARTH", "Warrior", 1800), ("EARTH", "Beast", 800), ("FIRE", "Pyro", 1700)],
    },
}

def _encode(t):
    pa = {d: [AM[c[0]] for c in t[d]] for d in t}
    pr = {d: [RM[c[1]] for c in t[d]] for d in t}
    pk = {d: [KM.get(c[2], -99) for c in t[d]] for d in t}
    return pa, pr, pk

ENC = {name: _encode(t) for name, t in TEMPLATES.items()}


def _round_scores(idx, pa, pr, pk):
    """给定开奖索引 idx(n,3)，返回该场在【相加】与【取最高】两模型下的单场得分 (add, mx)。"""
    wa = ATTR[idx]; wr = RACE[idx]; wk = ATK[idx]
    add_days = []; max_days = []
    for d in (1, 2, 3):
        ma = sum(((wa == pa[d][i]).any(1)).astype(np.int32) for i in range(3))
        mr = sum(((wr == pr[d][i]).any(1)).astype(np.int32) for i in range(3))
        mk = sum(((wk == pk[d][i]).any(1)).astype(np.int32) for i in range(3))
        ra = ARW[ma]; rr = RRW[mr]; rk = KRW[mk]
        add_days.append(ra + rr + rk)                       # 旧：相加
        max_days.append(np.maximum(ra, np.maximum(rr, rk))) # 新：取最高一项
    add_r = np.maximum.reduce(add_days)   # 场内取最高天
    max_r = np.maximum.reduce(max_days)
    return add_r, max_r


def worker(args):
    seed, n = args
    rng = np.random.default_rng(seed)
    # 直方图：相加模型 0..750，取最高模型 0..300
    hist = {name: {"add": np.zeros(751, np.int64), "max": np.zeros(301, np.int64)} for name in ENC}
    sub = 500_000
    done = 0
    while done < n:
        m = min(sub, n - done)
        idx = rng.integers(0, NMON, size=(m, 3))
        while True:  # 开奖三张互不相同
            dup = (idx[:, 0] == idx[:, 1]) | (idx[:, 1] == idx[:, 2]) | (idx[:, 0] == idx[:, 2])
            c = int(dup.sum())
            if c == 0:
                break
            idx[dup] = rng.integers(0, NMON, size=(c, 3))
        for name, (pa, pr, pk) in ENC.items():
            add_r, max_r = _round_scores(idx, pa, pr, pk)
            hist[name]["add"] += np.bincount(add_r, minlength=751)
            hist[name]["max"] += np.bincount(max_r, minlength=301)
        done += m
    return hist


def _stats_from_hist(counts):
    """单场直方图 → 单场期望，再卷积3次得到9天(3场)总分布 → 9天期望与各分位保底。"""
    total = counts.sum()
    pmf = counts / total
    vals = np.arange(len(pmf))
    round_mean = float((pmf * vals).sum())

    # 3 场独立同分布之和：pmf 自卷积两次
    total_pmf = np.convolve(np.convolve(pmf, pmf), pmf)  # 长度 3*(len-1)+1
    tvals = np.arange(len(total_pmf))
    total_mean = float((total_pmf * tvals).sum())
    cdf = np.cumsum(total_pmf)

    def floor_at(conf):
        # conf 置信度保底 = (1-conf) 分位数：P(总分 >= x) = conf
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
    tasks = [(1000 + i, per) for i in range(NPROC)]
    print(f"[+] 卡池 {NMON} 张；{NPROC} 进程 × {per:,} = {per*NPROC:,} 次开奖仿真（官方取最高模型）...")

    with mp.Pool(NPROC) as pool:
        parts = pool.map(worker, tasks)

    # 汇总各进程直方图
    agg = {name: {"add": np.zeros(751, np.int64), "max": np.zeros(301, np.int64)} for name in ENC}
    for h in parts:
        for name in ENC:
            agg[name]["add"] += h[name]["add"]
            agg[name]["max"] += h[name]["max"]

    results = {"n_sims": per * NPROC, "n_monsters": NMON, "templates": {}}
    for name in ("v1", "v2"):
        add_stats = _stats_from_hist(agg[name]["add"])
        max_stats = _stats_from_hist(agg[name]["max"])
        results["templates"][name] = {"additive": add_stats, "max_official": max_stats}

    # 亡羊补牢混搭：第1场 = hyb_r1，第2/3场 = 2.0(v2)，三场分布卷积
    def _combine_three(c_r1, c_r2):
        p1 = c_r1 / c_r1.sum()
        p2 = c_r2 / c_r2.sum()
        tp = np.convolve(np.convolve(p1, p2), p2)
        tv = np.arange(len(tp)); cdf = np.cumsum(tp)
        fa = lambda conf: int(tv[min(int(np.searchsorted(cdf, 1 - conf)), len(tv) - 1)])
        return {"total_mean": round(float((tp * tv).sum()), 2),
                "floor_80": fa(.8), "floor_90": fa(.9), "floor_95": fa(.95), "floor_99": fa(.99)}
    results["hybrid_day1_is_v1"] = {
        "max_official": _combine_three(agg["hyb_r1"]["max"], agg["v2"]["max"]),
        "additive": _combine_three(agg["hyb_r1"]["add"], agg["v2"]["add"]),
    }

    # 单独再测一次属性鸽巢失效率（取最高模型下，单场仅看属性维度是否 >=70）
    rng = np.random.default_rng(999)
    NTEST = 5_000_000
    fail = {name: 0 for name in ENC}
    done = 0
    while done < NTEST:
        m = min(500_000, NTEST - done)
        idx = rng.integers(0, NMON, size=(m, 3))
        while True:
            dup = (idx[:, 0] == idx[:, 1]) | (idx[:, 1] == idx[:, 2]) | (idx[:, 0] == idx[:, 2])
            c = int(dup.sum())
            if c == 0:
                break
            idx[dup] = rng.integers(0, NMON, size=(c, 3))
        wa = ATTR[idx]
        for name in ("v1", "v2"):
            pa, pr, pk = ENC[name]
            attr_days = []
            for d in (1, 2, 3):
                ma = sum(((wa == pa[d][i]).any(1)).astype(np.int32) for i in range(3))
                attr_days.append(ARW[ma])
            best_attr = np.maximum.reduce(attr_days)
            fail[name] += int((best_attr < 70).sum())
        done += m
    for name in ("v1", "v2"):
        results["templates"][name]["attr_pigeonhole_fail_rate"] = round(fail[name] / NTEST * 100, 2)

    out = "corrected_sim_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("\n" + "=" * 78)
    print(" 官方『取最高』模型 一亿次仿真结果（9天=3场合计）")
    print("=" * 78)
    for name, label in [("v1", "1.0 方案"), ("v2", "2.0 两日划分")]:
        t = results["templates"][name]
        a = t["additive"]; x = t["max_official"]
        print(f"\n【{label}】")
        print(f"  相加模型(旧/错) 9天期望: {a['total_mean']:.1f} 钻")
        print(f"  取最高(官方/对) 9天期望: {x['total_mean']:.1f} 钻")
        print(f"  取最高保底: 80%={x['floor_80']}  90%={x['floor_90']}  95%={x['floor_95']}  99%={x['floor_99']}")
        print(f"  单场区间[min={x['round_min']}, max={x['round_max']}]  属性鸽巢(70/场)失效率: {t['attr_pigeonhole_fail_rate']}%")
    h = results["hybrid_day1_is_v1"]["max_official"]
    print(f"\n【亡羊补牢·Day1已交1.0，Day2/3切2.0】(取最高)")
    print(f"  9天期望: {h['total_mean']:.1f} 钻   保底 80%={h['floor_80']} 90%={h['floor_90']} 95%={h['floor_95']} 99%={h['floor_99']}")
    print(f"\n[+] 已写出: {os.path.abspath(out)}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
