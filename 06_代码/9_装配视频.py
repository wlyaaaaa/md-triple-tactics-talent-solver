# -*- coding: utf-8 -*-
"""
三战之才 2.0 成片装配（用用户自录 MP3 + faster-whisper 精准字幕 + MD BGM）
========================================================================
- 不做 TTS：直接用 scene1.mp3 / 2.mp3 … 11.mp3（曼波配音），按真实时长、不裁剪。
- 11 张分镜图 + 8 张报告 PDF 横屏整页（每页 3s 静音）。
- 字幕：faster-whisper 转写，拿段级时间戳出 SRT（失败回退用稿子按句比例切）。
- BGM：把文件名含 BGM 的 MD 曲（排除 chiptune）顺接铺底，vol 0.10，片尾淡出。
- 编码：先试 h264_nvenc，失败回退 libx264。
"""
import os, glob, subprocess, wave, shutil
import imageio_ffmpeg
import fitz
from PIL import Image
from io import BytesIO

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 3840, 2160
FPS = 24
PDF_DISPLAY = 3.0
BGM_VOL = 0.22
BGM_FADE = 1.5
OUTPUT = "三战之才2.0最优解_9天白嫖376钻【游戏王MD】.mp4"
PDF = "三战之才2.0纠错版策略报告.pdf"

SLIDES = ["scene01_homework.png", "scene02_emergency.png", "scene03_rules.png",
          "scene04_rewards.png", "scene05_pool.png", "scene06_audit.png",
          "scene07_floor.png", "scene08_pipeline.png", "scene09_pk.png",
          "scene10_ghost.png", "scene11_summary.png"]

# 锁定文案（11 段，与录音一致；block9 已为"二十钻"）—— 仅作字幕兜底/参考
SCRIPTS = {
    1: "行，废话不多说，先上图。这套九天白嫖三百七十六钻的配置全在这，先截后看。九天一个轮回，每天交三张怪兽，三天分别在暗、光、地这三个最高频属性上各押两张，照表里的属性、种族、攻击力进游戏搜就行。搜出来记一句，别交一眼就认识的大众脸，往下划到底，挑那张你没见过、画风最上古的凡骨怪，这步跟大奖有关，等会儿专门说。这数怎么来的、为啥这么押，往下看。",
    2: "已经按上期老表交了第一天的别慌，不用删号。你第一天里本来就有张暗，刚好顶新表第一天的暗位，后两天换成这版就行。这种混搭我跑过，期望还有三百六十八，就比满配少八钻，九成五照样到二百一，不亏。",
    3: "半分钟把规则讲透。这活动就是跟系统猜怪兽，九天三场、每场三天，你每天交三张、系统每场开三张，比属性、种族、攻击力。这有个最容易被坑的点，一天里这三项，只算你对得最好的一项，不相加。你属性中俩值七十、种族中俩值一百，系统只发那个最高的一百，不会一百七。一场三天也只取你最猛那天，另外两天白给，三场加一块才是总收益。这部分，就是作业表能稳定嫖到的那三百多钻。",
    4: "但还有个完全独立的东西，叫卡名大奖。你交的整张卡跟系统开的一模一样，就能分一个几百万钻的大奖池。注意，这玩意儿跟你押什么特征一毛钱关系没有，纯看脸，每张卡蒙中的概率都一样，差不多九千分之一。所以记住，表负责你的下限，大奖是天上掉彩票，两码事。",
    5: "挑词条不是拍脑袋。系统开奖全卡池随机抽，哪种卡多就越容易被抽到。我把这版能选的八千九百多张怪兽全扒了，暗、地、光仨属性占七成一，水风炎加起来不到三成，种族战士、机械、恶魔打头，攻击力零攻最多。所以表里每个词条，挑的都是出现率最高的特征，押的就是个概率。卡池里还有五张神属性、三幻神那几种，别看单张稀有，系统九天要开九张牌，整个活动撞上它大概千分之五，还是低，基本无视就行。",
    6: "那这版升在哪？先说上期我栽的俩跟头。一个是选了窄槽，上期那个光属性恶魔族一千五攻，听着合理，游戏里一共就五张卡，几万人挤这五张，真蒙中大奖也分得没剩几个。另一个更尴尬，有个词条游戏里根本搜不出卡，那位置直接废了。这版全拿真卡池校验过，挑的都是几十张打底的分类。核心在保底。",
    7: "很多人教你属性干净二分、套鸽巢原理散着投，这是错的。鸽巢数的是中奖卡有几张，可结算数的是你命中几张卡，你一天就放一张暗，系统开俩暗你也只算中一个，二十钻打发。正确做法反过来，在最高频的暗、光、地上每天各押两张，这仨占七成一，只要开奖冒出任意一个，那天就稳两张同属性命中、七十钻到手。靠这个，保底失效的概率压到百分之二点三，九成五的场都能稳到二百一，最差百分之九十九也有二百兜底。",
    8: "这数怎么来的？从YGOPRODeck这个第三方卡查站把数据全扒下来，剪掉空槽，贪心搜模板，最后三十二线程跑一亿次收敛出来，平均三百七十六，实战你当个三百七八十的区间就行，个位数是噪声。",
    9: "直接看对比，同样按官方规则，上期那套真实期望只有二百八十六，这版高频各押两张三百七十六，而那个听着很美的三天属性全不重复，跑出来才二百八十五，跟上期一个水平。为啥？属性摊太散，系统一错开，你每天就只能捡个二十钻。所以结论很干脆，分天集中押注，才是版本答案。",
    10: "回到那个几百万的卡名大奖。它是全服蒙中的人平分，你中奖率高低不重要，反正每张都是九千分之一，重要的是别跟人撞，撞的人越少，你分得越多。挑冷门三步，先排本家，烙印、深渊之兽、闪刀姬，再冷也有情怀党手滑交，再排手坑，灰流、增G、泡影，铁定有人交，最后专挑名字最长、画风最古早、屁效果没有的上古凡骨。游戏里输完特征点搜索，手指划到底，挑最眼生那张交。九个位置我各备了三张，懒得想直接抄。",
    11: "总结。照这版交，期望三百七十六、九成五保底二百一，交了第一天的后两天直接切，表保下限，大奖纯看脸、选冷门只为少跟人分。觉得有用就三连关注，下期见。",
}


def aud(i):
    return "scene1.mp3" if i == 1 else f"{i}.mp3"


def probe(path):
    r = subprocess.run([FF, "-i", path], stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    for ln in r.stderr.split("\n"):
        if "Duration:" in ln:
            p = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
    return 3.0


def silent_wav(path, dur, sr=44100):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"\x00" * (int(dur * sr) * 4))


def doc_canvas(doc_png, out_png):
    im = Image.open(doc_png).convert("RGB")
    w = int(H * im.width / im.height)
    im = im.resize((w, H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    canvas.paste(im, (max(0, (W - w) // 2), 0))
    canvas.save(out_png)


def srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(durs, srt_path):
    """用锁定稿子（简体、零错字，与录音一致）按句切，配每场真实时长出 SRT。
    比 whisper 听写更准：MP3 本就是 TTS 念这份稿子，文本即真值。"""
    entries = []
    offset = 0.0
    for i in range(1, 12):
        sents = _chunks(SCRIPTS[i])
        tot = sum(len(x) for x in sents) or 1
        t = offset
        for s in sents:
            d = durs[i] * len(s) / tot
            entries.append((t, t + d, s))
            t += d
        offset += durs[i]
    with open(srt_path, "w", encoding="utf-8") as f:
        for n, (st, en, tx) in enumerate(entries, 1):
            f.write(f"{n}\n{srt_time(st)} --> {srt_time(en)}\n{tx}\n\n")
    return len(entries)


def _chunks(text, target=18):
    """按标点切碎后贪心合并到 ~target 字一条，避免字幕一闪而过。"""
    import re
    parts = [p for p in re.split(r"(?<=[。！？，、])", text) if p.strip()]
    out, cur = [], ""
    for p in parts:
        cur += p
        if len(cur) >= target or cur.endswith(("。", "！", "？")):
            out.append(cur); cur = ""
    if cur:
        if out and len(cur) < 8:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def encode_clip(img, audio, out_clip, dur):
    inp = [FF, "-loop", "1", "-framerate", str(FPS), "-i", img, "-i", audio]
    tail = ["-t", f"{dur:.3f}", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2", "-y", out_clip]
    nv = inp + ["-c:v", "h264_nvenc", "-preset", "p4", "-qp", "20"] + tail
    r = subprocess.run(nv, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if r.returncode == 0 and os.path.exists(out_clip) and os.path.getsize(out_clip) > 1000:
        return "nvenc"
    x = inp + ["-c:v", "libx264", "-preset", "fast", "-crf", "20"] + tail
    r = subprocess.run(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(f"编码失败 {out_clip}:\n{r.stderr.decode('utf-8','ignore')[-400:]}")
    return "libx264"


def main():
    # —— 万事俱备自检 ——
    print("=" * 60 + "\n[0] 自检")
    miss = []
    for s in SLIDES:
        if not os.path.exists(os.path.join("v2_frames", s)): miss.append(s)
    for i in range(1, 12):
        if not os.path.exists(aud(i)): miss.append(aud(i))
    docs = sorted(glob.glob(os.path.join("v2_frames", "doc_p*.png")))
    if not docs: miss.append("doc_p*.png")
    bgms = [f for f in sorted(glob.glob("*[Bb][Gg][Mm]*.mp3")) if "chiptune" not in f]
    if not bgms: miss.append("含BGM的音频")
    if not os.path.exists(PDF): miss.append(PDF)
    if miss:
        print("  [x] 缺少：", miss); return
    print(f"  [v] 11图+11音+{len(docs)}PDF页+{len(bgms)}BGM 齐：{[os.path.basename(b) for b in bgms]}")

    # —— 1. 帧 ——
    print("[1] 准备帧")
    for i, s in enumerate(SLIDES, 1):
        shutil.copy2(os.path.join("v2_frames", s), f"frame{i}.png")
    for j, dp in enumerate(docs, 12):
        doc_canvas(dp, f"frame{j}.png")
    n_doc = len(docs)
    n_scene = 11 + n_doc

    # —— 2. 时长 + 字幕 ——
    print("[2] 探时长")
    durs = {i: probe(aud(i)) for i in range(1, 12)}
    for i in range(1, 12):
        print(f"  scene{i}: {durs[i]:.1f}s")
    narr = sum(durs.values())
    print(f"  人声合计 {narr:.0f}s；PDF {n_doc}页×{PDF_DISPLAY}s={n_doc*PDF_DISPLAY:.0f}s")
    print("[2.5] 字幕")
    n_srt = build_srt(durs, OUTPUT.replace(".mp4", ".srt"))
    print(f"  [v] SRT {n_srt} 条 → {OUTPUT.replace('.mp4','.srt')}")

    # —— 3. 逐场编码 ——
    print("[3] 编码各场")
    for i in range(1, 12):
        silent = None
        enc = encode_clip(f"frame{i}.png", aud(i), f"clip_{i:02d}.mp4", durs[i])
    for k in range(n_doc):
        sid = 12 + k
        wavp = f"sil_{sid}.wav"; silent_wav(wavp, PDF_DISPLAY)
        encode_clip(f"frame{sid}.png", wavp, f"clip_{sid:02d}.mp4", PDF_DISPLAY)
    print(f"  [v] {n_scene} 段编码完成（编码器: {enc} 等）")

    # —— 4. 拼接 ——
    print("[4] 拼接")
    with open("concat.txt", "w", encoding="utf-8") as f:
        for sid in list(range(1, 12)) + list(range(12, 12 + n_doc)):
            f.write(f"file 'clip_{sid:02d}.mp4'\n")
    subprocess.run([FF, "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "-y", "novoice_tmp.mp4"],
                   stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True)
    total = narr + n_doc * PDF_DISPLAY

    # —— 5. BGM 顺接 + 混音 ——
    print("[5] BGM 混音")
    with open("bgm_list.txt", "w", encoding="utf-8") as f:
        for b in bgms:
            f.write(f"file '{b}'\n")
    subprocess.run([FF, "-f", "concat", "-safe", "0", "-i", "bgm_list.txt", "-c:a", "libmp3lame", "-q:a", "2",
                    "-y", "bgm_combined.mp3"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True)
    fade_start = max(0.0, total - BGM_FADE)
    if os.path.exists(OUTPUT): os.remove(OUTPUT)
    mix = [FF, "-i", "novoice_tmp.mp4", "-stream_loop", "-1", "-i", "bgm_combined.mp3",
           "-filter_complex",
           f"[1:a]volume={BGM_VOL},afade=t=out:st={fade_start:.2f}:d={BGM_FADE}[bg];[0:a][bg]amix=inputs=2:duration=first:normalize=0[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-y", OUTPUT]
    r = subprocess.run(mix, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if r.returncode != 0:
        print("  [x] 混音失败:\n", r.stderr.decode("utf-8", "ignore")[-500:]); return

    # —— 6. 清理 ——
    for i in range(1, 12 + n_doc):
        for p in (f"frame{i}.png", f"clip_{i:02d}.mp4", f"sil_{i+11}.wav"):
            if os.path.exists(p): os.remove(p)
    for p in ("concat.txt", "bgm_list.txt", "bgm_combined.mp3", "novoice_tmp.mp4"):
        if os.path.exists(p): os.remove(p)

    sz = os.path.getsize(OUTPUT) / (1024 * 1024)
    print("=" * 60)
    print(f"  [v] 成片：{OUTPUT}")
    print(f"  时长 {total:.0f}s（{total/60:.1f}分） | 大小 {sz:.0f}MB | 字幕 {OUTPUT.replace('.mp4','.srt')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
