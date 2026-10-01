"""梅花易数起卦（数字 / 时间 / 测字起卦，先天八卦数）。"""
from datetime import datetime

from lunar_python import Solar

from app.divination.bagua import TRIGRAM_BY_NUM, TRIGRAMS, hexagram_from_lines, _full_name
from app.divination.naming import _CHAR_INDEX
from app.schemas import MeiHuaRequest

# 十二地支在「数」上的序数（子=1 ... 亥=12）
ZHI_NUM = {"子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
           "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12}

# 常用汉字笔画表（测字起卦用，按简体/现代通用笔画）。表外字会如实提示，不做猜测。
# 注：梅花易数测字以「数」入卦，采用简体笔画；起名/测名的五格数理用康熙笔画（见 naming.py），两者用途不同、基准各异，均已注明。
STROKES = {
    "一": 1, "二": 2, "三": 3, "四": 5, "五": 4, "六": 4, "七": 2, "八": 2, "九": 2, "十": 2,
    "人": 2, "大": 3, "小": 3, "上": 3, "下": 3, "中": 4, "天": 4, "地": 6, "山": 3, "水": 4,
    "火": 4, "木": 4, "金": 8, "土": 3, "风": 4, "雷": 13, "电": 5, "云": 4, "雨": 8, "雪": 11,
    "日": 4, "月": 4, "星": 9, "明": 8, "阳": 6, "阴": 6, "春": 9, "夏": 10, "秋": 9, "冬": 5,
    "东": 5, "南": 9, "西": 6, "北": 5, "前": 9, "后": 6, "左": 5, "右": 5, "里": 7, "外": 5,
    "爱": 10, "情": 11, "婚": 11, "缘": 12, "财": 7, "富": 12, "贵": 9, "运": 7, "命": 8, "生": 5,
    "死": 6, "病": 10, "安": 6, "平": 5, "吉": 6, "凶": 4, "福": 13, "禄": 12, "寿": 7, "喜": 12,
    "心": 4, "意": 13, "愿": 14, "梦": 11, "想": 13, "事": 8, "业": 5, "成": 6, "败": 8, "得": 11,
    "失": 5, "去": 5, "来": 7, "归": 5, "行": 6, "走": 7, "住": 7, "迁": 6, "移": 11, "动": 6,
    "家": 10, "房": 8, "宅": 6, "门": 3, "车": 4, "船": 11, "路": 13, "桥": 10, "井": 4, "田": 5,
    "牛": 4, "马": 3, "羊": 6, "狗": 8, "猫": 11, "鸟": 5, "鱼": 8, "龙": 5, "虎": 8, "凤": 4,
    "男": 7, "女": 3, "父": 4, "母": 5, "子": 3, "儿": 2, "老": 6, "少": 4, "兄": 5, "弟": 7,
    "姐": 8, "妹": 8, "你": 7, "我": 7, "他": 5, "她": 6, "友": 4, "朋": 8, "客": 9, "主": 5,
    "学": 8, "考": 6, "试": 8, "工": 3, "作": 7, "职": 11, "位": 7, "升": 4, "调": 10, "换": 10,
    "钱": 10, "债": 10, "房": 8, "车": 4, "票": 11, "股": 8, "投": 7, "资": 10, "赚": 14, "赔": 12,
    "健": 10, "康": 11, "医": 7, "药": 9, "酒": 10, "茶": 9, "饭": 7, "米": 6, "菜": 11, "肉": 6,
    "张": 7, "王": 4, "李": 7, "刘": 6, "陈": 7, "杨": 7, "黄": 11, "赵": 9, "周": 8, "吴": 7,
    "徐": 10, "孙": 6, "胡": 9, "朱": 6, "高": 10, "林": 8, "何": 7, "郭": 10, "马": 3, "罗": 8,
    "梁": 11, "宋": 7, "郑": 8, "谢": 12, "韩": 12, "唐": 10, "冯": 5, "于": 3, "董": 12, "萧": 11,
}


def _num_to_trigram(n: int) -> str:
    """数字转先天八卦（余 0 作 8 坤）。"""
    r = n % 8
    if r == 0:
        r = 8
    return TRIGRAM_BY_NUM[r]


def _dong_from(num: int) -> int:
    """数字求动爻（1~6）。"""
    r = num % 6
    return 6 if r == 0 else r


def _build_lines(lower: str, upper: str, dong: int):
    """由上下卦与动爻位，生成本卦六爻与变卦六爻。dong: 动爻位 1~6（自下而上）。"""
    lower_bits = TRIGRAMS[lower]["binary"]
    upper_bits = TRIGRAMS[upper]["binary"]
    lines = []
    for i in range(3):
        lines.append((lower_bits >> i) & 1)
    for i in range(3):
        lines.append((upper_bits >> i) & 1)
    ben = lines[:]
    bian = lines[:]
    bian[dong - 1] ^= 1
    return ben, bian, dong


def _result(ben, bian, dong):
    ben_info = hexagram_from_lines(ben)
    bian_info = hexagram_from_lines(bian)
    # 互卦：2,3,4 爻为下互，3,4,5 爻为上互（均自下而上）
    hu_lower = [ben[1], ben[2], ben[3]]
    hu_upper = [ben[2], ben[3], ben[4]]
    hu = hexagram_from_lines(hu_lower + hu_upper)
    # 体用：动爻在上卦则用为上卦、体为下卦，反之亦然
    if dong <= 3:
        ti, yong = "下卦", "上卦"
    else:
        ti, yong = "上卦", "下卦"
    return {
        "ben": ben_info,
        "hu": hu,
        "bian": bian_info,
        "dong_yao": dong,
        "ti": ti,
        "yong": yong,
    }


def compute_meihua(req: MeiHuaRequest) -> dict:
    extra = None
    if req.type == "number":
        nums = [abs(int(n)) for n in (req.numbers or []) if n]
        if not nums:
            raise ValueError("数字起卦需要至少 1 个数字")
        nums = nums[:3]
        if len(nums) == 1:
            upper = lower = _num_to_trigram(nums[0])
            dong = _dong_from(nums[0])
        elif len(nums) == 2:
            upper, lower = _num_to_trigram(nums[0]), _num_to_trigram(nums[1])
            dong = _dong_from(nums[0] + nums[1])
        else:
            upper, lower = _num_to_trigram(nums[0]), _num_to_trigram(nums[1])
            dong = _dong_from(nums[2])
        method = f"数字起卦（{nums}）"

    elif req.type == "time":
        dt = datetime.strptime((req.time or "").strip(), "%Y-%m-%d %H:%M")
        lunar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).getLunar()
        # 农历月、日；时辰序数；年支序数
        month = abs(lunar.getMonth())
        day = lunar.getDay()
        hour_zhi = lunar.getTimeZhi()
        year_zhi = lunar.getYearZhi()
        shichen = ZHI_NUM[hour_zhi]
        year_num = ZHI_NUM[year_zhi]
        upper_num = year_num + month + day
        lower_num = upper_num + shichen
        upper = _num_to_trigram(upper_num)
        lower = _num_to_trigram(lower_num)
        dong = _dong_from(lower_num)
        method = f"时间起卦（农历{lunar.getYearInGanZhi()}年 {month}月{day}日 {hour_zhi}时）"

    else:  # word
        word = (req.word or "").strip()
        if not word:
            raise ValueError("测字需要提供汉字")
        if len(word) > 2:
            raise ValueError("测字请写 1~2 个字")
        strokes = []
        chars = []
        for ch in word:
            s = STROKES.get(ch)
            if s is None:
                s = _CHAR_INDEX.get(ch, {}).get("strokes")
            if s is None:
                raise ValueError(f"「{ch}」不在笔画库中，请换一个字或改用数字/时间起卦")
            wuxing = _CHAR_INDEX.get(ch, {}).get("wuxing")
            strokes.append(s)
            chars.append({"char": ch, "strokes": s, "wuxing": wuxing})
        if len(strokes) == 1:
            upper = lower = _num_to_trigram(strokes[0])
            dong = _dong_from(strokes[0])
        else:
            upper, lower = _num_to_trigram(strokes[0]), _num_to_trigram(strokes[1])
            dong = _dong_from(sum(strokes))
        method = f"测字起卦（「{word}」笔画 {strokes}）"
        extra = {"word": word, "chars": chars}

    ben, bian, dong = _build_lines(lower, upper, dong)
    res = _result(ben, bian, dong)
    res["method"] = method
    if extra:
        res["extra"] = extra
    return res
