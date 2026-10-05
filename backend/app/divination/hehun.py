"""八字合婚：两人八字配对分析（生肖、纳音、日柱、五行互补）。"""
from lunar_python import Lunar, Solar

from app.divination.bagua import SHENG, KE
from app.schemas import BaziRequest


def _to_lunar(req: BaziRequest) -> Lunar:
    if req.calendar == "lunar":
        return Lunar.fromYmdHms(req.year, req.month, req.day, req.hour, req.minute, 0)
    return Solar.fromYmdHms(req.year, req.month, req.day, req.hour, req.minute, 0).getLunar()


# 生肖（地支）关系表
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
         "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
LIUCHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
            "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
SANHE = [{"申", "子", "辰"}, {"亥", "卯", "未"}, {"寅", "午", "戌"}, {"巳", "酉", "丑"}]
XING = [{"寅", "巳", "申"}, {"丑", "戌", "未"}, {"子", "卯"}]
HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
       "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}

# 天干五合
GAN_HE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛",
          "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}


def _zhi_relation(a, b):
    """两地支的关系：六合/六冲/三合/相刑/相害/无。"""
    if LIUHE.get(a) == b:
        return "六合（大吉）"
    if LIUCHONG.get(a) == b:
        return "六冲（需调和）"
    if any(a in s and b in s for s in SANHE):
        return "三合（吉）"
    if any(a in s and b in s for s in XING):
        return "相刑（需注意）"
    if HAI.get(a) == b:
        return "相害（小摩擦）"
    return "无冲合"


def compute_hehun(male: BaziRequest, female: BaziRequest) -> dict:
    ml = _to_lunar(male)
    fl = _to_lunar(female)
    me = ml.getEightChar()
    fe = fl.getEightChar()

    m_sx = ml.getYearShengXiao()
    f_sx = fl.getYearShengXiao()
    m_zhi = ml.getYearZhi()
    f_zhi = fl.getYearZhi()

    # 1. 生肖关系
    sx_rel = _zhi_relation(m_zhi, f_zhi)

    # 2. 年柱纳音五行生克
    m_nayin = me.getYearNaYin()
    f_nayin = fe.getYearNaYin()
    # 纳音五行取末位（如「海中金」→金）
    m_nw = m_nayin[-1]
    f_nw = f_nayin[-1]
    if m_nw == f_nw:
        nayin_rel = f"同属「{m_nw}」，比和"
    elif SHENG.get(m_nw) == f_nw:
        nayin_rel = f"男「{m_nw}」生女「{f_nw}」，相生（吉）"
    elif SHENG.get(f_nw) == m_nw:
        nayin_rel = f"女「{f_nw}」生男「{m_nw}」，相生（吉）"
    elif KE.get(m_nw) == f_nw:
        nayin_rel = f"男「{m_nw}」克女「{f_nw}」，相克（需注意）"
    else:
        nayin_rel = f"女「{f_nw}」克男「{m_nw}」，相克（需注意）"

    # 3. 日柱天干地支关系
    m_day_gan = me.getDayGan()
    f_day_gan = fe.getDayGan()
    m_day_zhi = me.getDayZhi()
    f_day_zhi = fe.getDayZhi()
    gan_rel = "天干相合（吉）" if GAN_HE.get(m_day_gan) == f_day_gan else "天干无合"
    zhi_rel = _zhi_relation(m_day_zhi, f_day_zhi)

    # 4. 五行互补：两人八字五行加总，看覆盖是否均衡
    def _wuxing_count(ec):
        counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        for w in [ec.getYearWuXing(), ec.getMonthWuXing(), ec.getDayWuXing(), ec.getTimeWuXing()]:
            counts[w[0]] = counts.get(w[0], 0) + 1
            counts[w[1]] = counts.get(w[1], 0) + 1
        return counts

    mc = _wuxing_count(me)
    fc = _wuxing_count(fe)
    total = {k: mc[k] + fc[k] for k in mc}
    missing = [k for k, v in total.items() if v == 0]
    balance = "五行齐全、较为均衡" if not missing else f"两人合起来缺「{'、'.join(missing)}」"

    return {
        "male": {"shengxiao": m_sx, "zhi": m_zhi, "nayin": m_nayin, "day_ganzhi": me.getDay()},
        "female": {"shengxiao": f_sx, "zhi": f_zhi, "nayin": f_nayin, "day_ganzhi": fe.getDay()},
        "shengxiao_rel": f"{m_sx}{f_sx}：{sx_rel}",
        "nayin_rel": nayin_rel,
        "day_gan_rel": f"日干{m_day_gan}{f_day_gan}：{gan_rel}",
        "day_zhi_rel": f"日支{m_day_zhi}{f_day_zhi}：{zhi_rel}",
        "wuxing_balance": balance,
    }
