"""太岁查询：按出生年支与流年支的固定地支关系判定犯太岁类型。

仅做传统民俗层面的确定性查询；「化解」无统一标准，本模块不做效果承诺。
"""
from datetime import date

from lunar_python import Solar

from app.schemas import TaiSuiRequest

ZHI = "子丑寅卯辰巳午未申酉戌亥"

SHENGXIAO = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

# 三刑（组内两两相刑）+ 自刑（辰午酉亥见本支）
SELF_XING = {"辰", "午", "酉", "亥"}
XING_PAIRS = {
    frozenset(p) for p in [
        ("寅", "巳"), ("巳", "申"), ("寅", "申"),   # 恃势之刑
        ("丑", "戌"), ("戌", "未"), ("丑", "未"),   # 无恩之刑
        ("子", "卯"),                               # 无礼之刑
    ]
}

# 六害、六破、六合
HAI_PAIRS = {
    frozenset(p) for p in [
        ("子", "未"), ("丑", "午"), ("寅", "巳"),
        ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
    ]
}
PO_PAIRS = {
    frozenset(p) for p in [
        ("子", "酉"), ("丑", "辰"), ("寅", "亥"),
        ("卯", "午"), ("巳", "申"), ("未", "戌"),
    ]
}
HE_PAIRS = {
    frozenset(p) for p in [
        ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
        ("辰", "酉"), ("巳", "申"), ("午", "未"),
    ]
}

NOTES = {
    "值太岁": "本命年。传统民俗视为变动之年，宜稳守、少冲动，注意健康与情绪。",
    "冲太岁": "流年支与出生年支相冲。传统民俗视为动荡、变动之象，出行与重大决策宜多加谨慎。",
    "刑太岁": "流年支与出生年支相刑。传统民俗视为口舌是非、人际摩擦之象，宜谨言慎行。",
    "害太岁": "流年支与出生年支相害。传统民俗视为暗损、合作不顺之象，宜防人之心、慎签合约。",
    "破太岁": "流年支与出生年支相破。传统民俗视为破耗、计划受阻之象，宜守成、避免冒进。",
    "合太岁": "流年支与出生年支六合。传统视为和合之象，并非犯太岁，人际合作相对顺遂。",
}

FAN = ("值太岁", "冲太岁", "刑太岁", "害太岁", "破太岁")


def _year_pillar(year: int, month: int | None = None, day: int | None = None) -> str:
    """取某公历年的年柱干支；年界按立春（6 月 1 日必在立春后）。"""
    solar = Solar.fromYmd(year, month, day) if month and day else Solar.fromYmd(year, 6, 1)
    return solar.getLunar().getEightChar().getYear()


def _is_chong(a: str, b: str) -> bool:
    return (ZHI.index(a) - ZHI.index(b)) % 12 == 6


def _relations(birth_zhi: str, year_zhi: str) -> list:
    rel = []
    if birth_zhi == year_zhi:
        rel.append("值太岁")
    if _is_chong(birth_zhi, year_zhi):
        rel.append("冲太岁")
    pair = frozenset((birth_zhi, year_zhi))
    if pair in XING_PAIRS or (birth_zhi == year_zhi and birth_zhi in SELF_XING):
        rel.append("刑太岁")
    if pair in HAI_PAIRS:
        rel.append("害太岁")
    if pair in PO_PAIRS:
        rel.append("破太岁")
    if pair in HE_PAIRS:
        rel.append("合太岁")
    return rel


def _summary(relations: list) -> str:
    fan = [r for r in relations if r in FAN]
    if fan:
        return f"本年你犯「{'、'.join(fan)}」。以上为传统民俗说法，供文化参考。"
    if "合太岁" in relations:
        return "本年与你的出生年支六合，属合太岁，传统上不算犯太岁。"
    return "本年与你的出生年支无明显冲、刑、害、破，传统上不犯太岁。"


def compute_taisui(req: TaiSuiRequest) -> dict:
    if (req.month is None) != (req.day is None):
        raise ValueError("出生月份与日期需同时提供，或都不提供")

    birth_gz = _year_pillar(req.year, req.month, req.day)
    query_year = req.query_year or date.today().year
    query_gz = _year_pillar(query_year)

    birth_zhi, year_zhi = birth_gz[1], query_gz[1]
    relations = _relations(birth_zhi, year_zhi)

    return {
        "birth": {
            "year": req.year,
            "ganzhi": birth_gz,
            "zhi": birth_zhi,
            "shengxiao": SHENGXIAO[birth_zhi],
        },
        "query": {
            "year": query_year,
            "ganzhi": query_gz,
            "zhi": year_zhi,
            "shengxiao": SHENGXIAO[year_zhi],
        },
        "relations": relations,
        "details": [{"name": r, "note": NOTES[r]} for r in relations],
        "is_fan": any(r in FAN for r in relations),
        "summary": _summary(relations),
        "disclaimer": "本结果仅按地支关系做确定性查询。所谓「化解」无统一标准，本系统不提供效果承诺。",
    }
