"""八字四柱排盘（基于 lunar-python 历法内核）。"""
from lunar_python import Lunar, Solar

from app.schemas import BaziRequest


def _to_solar(req: BaziRequest) -> Solar:
    """把请求（公历/农历）统一转成公历 Solar。"""
    if req.calendar == "lunar":
        lunar = Lunar.fromYmdHms(req.year, req.month, req.day, req.hour, req.minute, 0)
        return lunar.getSolar()
    return Solar.fromYmdHms(req.year, req.month, req.day, req.hour, req.minute, 0)


def _count_wuxing(four: list) -> dict:
    """统计四柱天干地支的五行数量，用于判断五行缺失（仅供喜用神参考）。"""
    counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for w in four:
        counts[w] = counts.get(w, 0) + 1
    return counts


def compute_bazi(req: BaziRequest) -> dict:
    solar = _to_solar(req)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    gender_code = 1 if req.gender == "男" else 0
    yun = ec.getYun(gender_code)

    pillars = [
        {
            "name": "年柱", "ganzhi": ec.getYear(), "gan": ec.getYearGan(), "zhi": ec.getYearZhi(),
            "wuxing": ec.getYearWuXing(), "nayin": ec.getYearNaYin(),
            "hide_gan": ec.getYearHideGan(), "shishen_gan": ec.getYearShiShenGan(),
            "shishen_zhi": ec.getYearShiShenZhi(), "dishi": ec.getYearDiShi(),
            "xun": ec.getYearXun(), "xunkong": ec.getYearXunKong(),
        },
        {
            "name": "月柱", "ganzhi": ec.getMonth(), "gan": ec.getMonthGan(), "zhi": ec.getMonthZhi(),
            "wuxing": ec.getMonthWuXing(), "nayin": ec.getMonthNaYin(),
            "hide_gan": ec.getMonthHideGan(), "shishen_gan": ec.getMonthShiShenGan(),
            "shishen_zhi": ec.getMonthShiShenZhi(), "dishi": ec.getMonthDiShi(),
            "xun": ec.getMonthXun(), "xunkong": ec.getMonthXunKong(),
        },
        {
            "name": "日柱", "ganzhi": ec.getDay(), "gan": ec.getDayGan(), "zhi": ec.getDayZhi(),
            "wuxing": ec.getDayWuXing(), "nayin": ec.getDayNaYin(),
            "hide_gan": ec.getDayHideGan(), "shishen_gan": ec.getDayShiShenGan(),
            "shishen_zhi": ec.getDayShiShenZhi(), "dishi": ec.getDayDiShi(),
            "xun": ec.getDayXun(), "xunkong": ec.getDayXunKong(),
        },
        {
            "name": "时柱", "ganzhi": ec.getTime(), "gan": ec.getTimeGan(), "zhi": ec.getTimeZhi(),
            "wuxing": ec.getTimeWuXing(), "nayin": ec.getTimeNaYin(),
            "hide_gan": ec.getTimeHideGan(), "shishen_gan": ec.getTimeShiShenGan(),
            "shishen_zhi": ec.getTimeShiShenZhi(), "dishi": ec.getTimeDiShi(),
            "xun": ec.getTimeXun(), "xunkong": ec.getTimeXunKong(),
        },
    ]

    da_yun = [
        {"age": d.getStartAge(), "ganzhi": d.getGanZhi(), "start_year": d.getStartYear()}
        for d in yun.getDaYun()
        if d.getGanZhi()
    ]

    # 每柱五行是「干五行 + 支五行」的两字串（如「土木」），拆成单字后统计
    four_wuxing = []
    for p in pillars:
        w = p["wuxing"]
        four_wuxing.append(w[0])  # 天干五行
        four_wuxing.append(w[1])  # 地支五行
    wuxing_count = _count_wuxing(four_wuxing)
    missing = [w for w, c in wuxing_count.items() if c == 0]

    return {
        "solar": solar.toYmdHms(),
        "lunar": lunar.toString(),
        "shengxiao": lunar.getYearShengXiao(),
        "gender": req.gender,
        "day_master": ec.getDayGan(),           # 日主（日干）
        "pillars": pillars,
        "wuxing_count": wuxing_count,
        "missing_wuxing": missing,              # 五行缺失（参考）
        "ming_gong": {"ganzhi": ec.getMingGong(), "nayin": ec.getMingGongNaYin()},
        "shen_gong": ec.getShenGong(),
        "tai_yuan": {"ganzhi": ec.getTaiYuan(), "nayin": ec.getTaiYuanNaYin()},
        "tai_xi": ec.getTaiXi(),
        "qi_yun": {
            "forward": yun.isForward(),
            "start_year": yun.getStartYear(),
            "start_month": yun.getStartMonth(),
            "start_day": yun.getStartDay(),
            "start_solar": yun.getStartSolar().toYmd(),
        },
        "da_yun": da_yun,
    }
