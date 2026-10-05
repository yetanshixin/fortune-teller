"""数字测吉凶（手机号 / 车牌号等）：数字五行 + 八星磁场组合。"""

# 数字五行
NUM_WUXING = {
    "1": "水", "2": "土", "3": "木", "4": "木", "5": "土",
    "6": "金", "7": "金", "8": "土", "9": "火", "0": "土",
}

# 八星磁场：相邻两位组合的吉凶
JIXING = {
    "天医": ["13", "31", "68", "86", "49", "94", "27", "72"],
    "生气": ["14", "41", "67", "76", "39", "93", "28", "82"],
    "延年": ["19", "91", "78", "87", "34", "43", "26", "62"],
}
ZHONGXING = {
    "伏位": ["11", "22", "33", "44", "66", "77", "88", "99"],
}
XIONGXING = {
    "绝命": ["12", "21", "69", "96", "48", "84", "37", "73"],
    "五鬼": ["18", "81", "79", "97", "36", "63", "24", "42"],
    "六煞": ["16", "61", "47", "74", "38", "83", "29", "92"],
    "祸害": ["17", "71", "89", "98", "46", "64", "23", "32"],
}


def _magnetic(pair):
    for name, pairs in {**JIXING, **ZHONGXING, **XIONGXING}.items():
        if pair in pairs:
            return name
    return None


def compute_shuzi(number: str) -> dict:
    """数字测吉凶：拆解数字串，分析五行与相邻组合磁场。"""
    num = "".join(ch for ch in number if ch.isdigit())
    if not num:
        raise ValueError("请输入数字（手机号/车牌号等）")

    # 每个数字五行计数
    wuxing_count = {}
    for ch in num:
        w = NUM_WUXING[ch]
        wuxing_count[w] = wuxing_count.get(w, 0) + 1

    # 相邻组合磁场
    ji = []
    xiong = []
    for i in range(len(num) - 1):
        pair = num[i:i + 2]
        mag = _magnetic(pair)
        if mag in JIXING:
            ji.append((pair, mag))
        elif mag in XIONGXING:
            xiong.append((pair, mag))

    ji_count = len(ji)
    xiong_count = len(xiong)
    if ji_count > xiong_count:
        verdict = "偏吉"
    elif xiong_count > ji_count:
        verdict = "偏凶"
    else:
        verdict = "中平"

    return {
        "number": number,
        "digits": num,
        "wuxing_count": wuxing_count,
        "ji": ji,
        "xiong": xiong,
        "verdict": verdict,
    }
