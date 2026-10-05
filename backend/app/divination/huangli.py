"""黄历 / 择日查询（基于 lunar-python 历法内核）。"""
from lunar_python import Solar

from app.schemas import HuangLiRequest

# 青龙十二神（黄道黑道）：顺序固定，吉凶交错
SHI_ER_SHEN = [
    ("青龙", "吉"), ("明堂", "吉"), ("天刑", "凶"), ("朱雀", "凶"),
    ("金匮", "吉"), ("天德", "吉"), ("白虎", "凶"), ("玉堂", "吉"),
    ("天牢", "凶"), ("玄武", "凶"), ("司命", "吉"), ("勾陈", "凶"),
]
SHI_CHEN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
# 各日支「青龙」起始时辰索引（子=0）
_QINGLONG_START = {"子": 8, "午": 8, "丑": 10, "未": 10, "寅": 0, "申": 0,
                   "卯": 2, "酉": 2, "辰": 4, "戌": 4, "巳": 6, "亥": 6}


def compute_shichen(day_zhi: str) -> list:
    """某日十二时辰的黄道黑道吉凶（择时用）。"""
    start = _QINGLONG_START[day_zhi]
    result = []
    for i in range(12):
        name, luck = SHI_ER_SHEN[i]
        shi = SHI_CHEN[(start + i) % 12]
        result.append({"shi": shi, "shen": name, "luck": luck})
    return result


def compute_huangli(req: HuangLiRequest) -> dict:
    solar = Solar.fromYmd(req.year, req.month, req.day)
    lunar = solar.getLunar()

    return {
        "solar": solar.toYmd(),
        "lunar": lunar.toString(),
        "year_ganzhi": lunar.getYearInGanZhi(),
        "month_ganzhi": lunar.getMonthInGanZhi(),
        "day_ganzhi": lunar.getDayInGanZhi(),
        "shengxiao": lunar.getYearShengXiao(),
        "day_shengxiao": lunar.getDayShengXiao(),
        "nayin": lunar.getDayNaYin(),
        "zhi_xing": lunar.getZhiXing(),               # 建除十二值星
        "jiu_xing": lunar.getDayNineStar(),
        "peng_zu": {
            "gan": lunar.getPengZuGan(),
            "zhi": lunar.getPengZuZhi(),
        },
        "chong": lunar.getDayChongDesc(),
        "sha": lunar.getDaySha(),
        "lu": lunar.getDayLu(),
        "tian_shen": {
            "name": lunar.getDayTianShen(),
            "type": lunar.getDayTianShenType(),
            "luck": lunar.getDayTianShenLuck(),
        },
        "ji_shen": lunar.getDayJiShen(),
        "xiong_sha": lunar.getDayXiongSha(),
        "yi": lunar.getDayYi(),
        "ji": lunar.getDayJi(),
        "position": {
            "cai": lunar.getDayPositionCaiDesc(),
            "xi": lunar.getDayPositionXiDesc(),
            "fu": lunar.getDayPositionFuDesc(),
            "yang_gui": lunar.getDayPositionYangGuiDesc(),
            "yin_gui": lunar.getDayPositionYinGuiDesc(),
            "tai": lunar.getDayPositionTai(),
            "tai_sui": lunar.getDayPositionTaiSuiDesc(),
        },
        "xun": {"xun": lunar.getDayXun(), "xun_kong": lunar.getDayXunKong()},
        "shichen": compute_shichen(lunar.getDayZhi()),   # 十二时辰吉凶（择时）
        "matter": req.matter,
    }
