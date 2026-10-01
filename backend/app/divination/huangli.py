"""黄历 / 择日查询（基于 lunar-python 历法内核）。"""
from lunar_python import Solar

from app.schemas import HuangLiRequest


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
        "matter": req.matter,
    }
