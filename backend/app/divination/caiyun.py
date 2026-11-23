"""财运分析（基于八字十神、五行旺衰、大运流年的确定性量化模型）。

说明：本模块按子平命理的常见简化规则做量化（同党/异党、财星、食伤、比劫），
属传统文化参考，不是唯一标准；排盘数据确定性给出，解读由大模型负责。
"""
from datetime import date

from lunar_python import Solar
from lunar_python.util import LunarUtil

from app.divination.bazi import compute_bazi
from app.schemas import CaiYunRequest

# 五行生克
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # 我克

# 地支本气天干（用于大运/流年地支的十神判断）
ZHI_BENQI = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}

SHENGXIAO = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

CAI = ("正财", "偏财")
SHISHANG = ("食神", "伤官")
BIJIE = ("比肩", "劫财")
GUANSHA = ("正官", "七杀")


def _wx_of(sym: str) -> str:
    """天干或地支 → 五行（地支取本气五行）。"""
    if sym in LunarUtil.WU_XING_GAN:
        return LunarUtil.WU_XING_GAN[sym]
    return LunarUtil.WU_XING_ZHI[sym]


def _relation(wx: str, day_wx: str) -> str:
    """某五行相对日主五行的大类：比劫 / 印 / 食伤 / 财 / 官杀。"""
    if wx == day_wx:
        return "比劫"
    if SHENG[wx] == day_wx:      # 该五行生我 → 印
        return "印"
    if SHENG[day_wx] == wx:      # 我生该五行 → 食伤
        return "食伤"
    if KE[day_wx] == wx:         # 我克该五行 → 财
        return "财"
    return "官杀"


def _strength(pillars: list, day_gan: str) -> dict:
    """身强身弱：同党（比劫+印）vs 异党（食伤+财+官杀）加权。

    权重：天干 1，月支 3（得令最重要），其余地支 1。
    """
    day_wx = LunarUtil.WU_XING_GAN[day_gan]
    items = []
    for p in pillars:
        items.append((p["gan"], 1.0))
        items.append((p["zhi"], 3.0 if p["name"] == "月柱" else 1.0))

    total = sum(w for _, w in items)
    tong = 0.0
    detail = {"比劫": 0.0, "印": 0.0, "食伤": 0.0, "财": 0.0, "官杀": 0.0}
    for sym, w in items:
        rel = _relation(_wx_of(sym), day_wx)
        detail[rel] += w
        if rel in ("比劫", "印"):
            tong += w

    score = tong / total
    if score >= 0.55:
        level = "身强"
    elif score >= 0.48:
        level = "偏强"
    elif score >= 0.42:
        level = "中和"
    elif score >= 0.35:
        level = "偏弱"
    else:
        level = "身弱"

    return {
        "level": level,
        "score": round(score, 2),
        "tong_dang": round(tong, 1),
        "yi_dang": round(total - tong, 1),
        "detail": {k: round(v, 1) for k, v in detail.items()},
    }


def _count_shishen(pillars: list, names: tuple) -> int:
    """统计指定十神在四柱天干与地支藏干中的出现次数。"""
    n = 0
    for p in pillars:
        if p["shishen_gan"] in names:
            n += 1
        n += sum(1 for s in (p["shishen_zhi"] or []) if s in names)
    return n


def _cai_positions(pillars: list) -> list:
    """列出财星出现的位置。"""
    out = []
    for p in pillars:
        if p["shishen_gan"] in CAI:
            out.append(f"{p['name']}天干 {p['gan']}（{p['shishen_gan']}）")
        for ss in (p["shishen_zhi"] or []):
            if ss in CAI:
                out.append(f"{p['name']}地支 {p['zhi']} 藏干（{ss}）")
    return out


def _cai_weight(pillars: list, cai_wx: str) -> float:
    """财星五行在四柱中的加权力量：天干 1、月支 3、其他地支 1、藏干各 0.5。"""
    total = 0.0
    for p in pillars:
        if _wx_of(p["gan"]) == cai_wx:
            total += 1.0
        if _wx_of(p["zhi"]) == cai_wx:
            total += 3.0 if p["name"] == "月柱" else 1.0
        for hg in (p["hide_gan"] or []):
            if _wx_of(hg) == cai_wx:
                total += 0.5
    return total


def _tendency(gan_ss: str, zhi_ss: str) -> str:
    """大运/流年财运倾向描述。"""
    labels = []
    for ss in (gan_ss, zhi_ss):
        if ss in CAI:
            label = "财星临运：利求财、增收入"
        elif ss in SHISHANG:
            label = "食伤临运：生财之源，凭技艺进财"
        elif ss in BIJIE:
            label = "比劫临运：竞争分财，防合伙借贷破耗"
        elif ss in GUANSHA:
            label = "官杀临运：事业压力与责任，护财亦耗神"
        else:
            label = "印星临运：守成、贵人助力"
        if label not in labels:
            labels.append(label)
    return " / ".join(labels)


def _da_yun_analysis(da_yun: list, day_gan: str) -> list:
    out = []
    for y in da_yun:
        gz = y["ganzhi"]
        gan_ss = LunarUtil.SHI_SHEN[day_gan + gz[0]]
        zhi_ss = LunarUtil.SHI_SHEN[day_gan + ZHI_BENQI[gz[1]]]
        out.append({
            "age": y["age"],
            "ganzhi": gz,
            "gan_shishen": gan_ss,
            "zhi_shishen": zhi_ss,
            "tendency": _tendency(gan_ss, zhi_ss),
        })
    return out


def _liu_nian_analysis(query_year: int, day_gan: str) -> dict:
    ec = Solar.fromYmd(query_year, 6, 1).getLunar().getEightChar()
    gz = ec.getYear()
    gan_ss = LunarUtil.SHI_SHEN[day_gan + gz[0]]
    zhi_ss = LunarUtil.SHI_SHEN[day_gan + ZHI_BENQI[gz[1]]]
    return {
        "year": query_year,
        "ganzhi": gz,
        "zhi": gz[1],
        "shengxiao": SHENGXIAO[gz[1]],
        "gan_shishen": gan_ss,
        "zhi_shishen": zhi_ss,
        "tendency": _tendency(gan_ss, zhi_ss),
    }


def compute_caiyun(req: CaiYunRequest) -> dict:
    b = compute_bazi(req)
    pillars = b["pillars"]
    day_gan = b["day_master"]
    day_wx = LunarUtil.WU_XING_GAN[day_gan]

    strength = _strength(pillars, day_gan)

    cai_wx = KE[day_wx]
    cai_positions = _cai_positions(pillars)
    cai_weight = _cai_weight(pillars, cai_wx)
    if cai_weight >= 3.0:
        cai_level = "偏旺"
    elif cai_weight >= 1.5:
        cai_level = "中和"
    else:
        cai_level = "偏弱"

    shishang_count = _count_shishen(pillars, SHISHANG)
    bijie_count = _count_shishen(pillars, BIJIE)
    cai_count = len(cai_positions)
    sheng_cai = shishang_count > 0 and cai_count > 0
    duo_cai = bijie_count >= 3 and strength["level"] in ("身强", "偏强")

    patterns = []
    if strength["level"] in ("身强", "偏强") and cai_level == "偏旺":
        patterns.append("身强财旺——自身能担财，求财较有底气")
    if strength["level"] in ("身弱", "偏弱") and cai_level == "偏旺":
        patterns.append("财多身弱——财旺而自身承压，宜合伙借力、量力而行")
    if sheng_cai:
        patterns.append("食伤生财——宜凭专业技能、创意与人脉生财")
    if duo_cai:
        patterns.append("比劫偏多——竞争分财，合伙与借贷需谨慎")
    if cai_level == "偏弱":
        patterns.append("财星偏弱——财源需借食伤或大运流年引动")
    if not patterns:
        patterns.append("财星平顺——宜稳中求进，积少成多")

    query_year = req.query_year or date.today().year

    return {
        "solar": b["solar"],
        "lunar": b["lunar"],
        "gender": b["gender"],
        "shengxiao": b["shengxiao"],
        "day_master": day_gan,
        "day_master_wuxing": day_wx,
        "strength": strength,
        "cai": {
            "wuxing": cai_wx,
            "positions": cai_positions,
            "count": cai_count,
            "weight": round(cai_weight, 1),
            "level": cai_level,
        },
        "shishang": {"count": shishang_count, "sheng_cai": sheng_cai},
        "bijie": {"count": bijie_count, "duo_cai": duo_cai},
        "patterns": patterns,
        "da_yun": _da_yun_analysis(b["da_yun"], day_gan),
        "liu_nian": _liu_nian_analysis(query_year, day_gan),
        "notes": [
            "身强弱按同党（比劫+印）与异党（食伤+财+官杀）加权得出，月令权重最高，为简化量化模型。",
            "财星定位以日主所克五行为准；食伤生财、比劫夺财均按十神出现次数判断。",
            "本结果仅供传统文化参考，不构成投资建议。",
        ],
    }
