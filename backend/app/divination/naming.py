"""起名（五行补益 + 姓名学五格数理 + 字义参考）。

说明：汉字笔画按姓名学惯例（康熙字典笔画），五行属性按字形/字义/笔画综合取定，
均为姓名学参考数据；最终解读与定名建议交由大模型结合音韵、字义、文化内涵完成。
"""
from app.divination.bazi import compute_bazi
from app.schemas import NamingRequest

# 名字用字库：字、笔画(康熙)、五行、寓意、性别倾向(m/f/n)
CHARS = [
    # 男名倾向
    ("宇", 6, "土", "气度、宇宙、广阔", "m"),
    ("浩", 11, "水", "浩大、正直、宽广", "m"),
    ("轩", 10, "土", "气宇轩昂、不凡", "m"),
    ("铭", 14, "金", "铭记、出众、深刻", "m"),
    ("泽", 17, "水", "恩泽、润泽、仁厚", "m"),
    ("晨", 11, "火", "清晨、希望、朝气", "m"),
    ("睿", 14, "金", "聪慧、睿智、远见", "m"),
    ("翔", 12, "土", "飞翔、进取、自由", "m"),
    ("昊", 8, "火", "天空、博大、浩然", "m"),
    ("辰", 7, "土", "星辰、时运、生机", "m"),
    ("博", 12, "水", "博学、宽广、丰厚", "m"),
    ("毅", 15, "木", "坚毅、刚强、恒心", "m"),
    ("航", 10, "水", "航行、志向、远方", "m"),
    ("斌", 12, "水", "文质兼备、儒雅", "m"),
    ("骏", 17, "金", "骏马、出众、卓越", "m"),
    ("哲", 10, "火", "智慧、明理、通达", "m"),
    ("峰", 10, "土", "山峰、杰出、高远", "m"),
    ("霖", 16, "水", "甘霖、恩泽、滋润", "m"),
    ("煜", 13, "火", "光耀、明亮、兴旺", "m"),
    ("瑞", 13, "金", "祥瑞、吉祥、福气", "m"),
    ("辉", 15, "火", "光辉、照耀、显赫", "m"),
    ("志", 7, "火", "志向、抱负、坚定", "m"),
    ("弘", 5, "水", "弘扬、大度、气魄", "m"),
    ("俊", 9, "火", "俊秀、杰出、才貌", "m"),
    ("凯", 12, "木", "凯旋、胜利、欢欣", "m"),
    # 女名倾向
    ("涵", 12, "水", "涵养、包容、沉静", "f"),
    ("悦", 11, "金", "喜悦、欢愉、温婉", "f"),
    ("欣", 8, "木", "欣喜、蓬勃、生机", "f"),
    ("婷", 12, "火", "亭亭玉立、优雅", "f"),
    ("萱", 15, "木", "忘忧、萱草、恬静", "f"),
    ("梓", 11, "木", "梓树、家乡、端庄", "f"),
    ("怡", 9, "土", "愉悦、和乐、怡然", "f"),
    ("雨", 8, "水", "雨露、清新、灵动", "f"),
    ("晴", 12, "火", "晴朗、明媚、开朗", "f"),
    ("彤", 7, "火", "红色、热烈、明丽", "f"),
    ("诗", 13, "金", "诗意、文雅、灵秀", "f"),
    ("雅", 12, "木", "优雅、高尚、文静", "f"),
    ("韵", 19, "土", "韵律、气质、风韵", "f"),
    ("思", 9, "金", "思念、睿智、才思", "f"),
    ("瑶", 15, "火", "美玉、珍贵、美好", "f"),
    ("静", 16, "金", "宁静、文静、恬淡", "f"),
    ("雪", 11, "水", "纯洁、高洁、清雅", "f"),
    ("敏", 11, "水", "聪敏、灵活、勤勉", "f"),
    ("琳", 13, "木", "美玉、美好、清雅", "f"),
    ("琪", 13, "木", "美玉、珍奇、灵秀", "f"),
    ("蕊", 18, "木", "花蕊、娇美、芬芳", "f"),
    ("菲", 14, "木", "芬芳、美好、雅致", "f"),
    ("妍", 7, "水", "美丽、娇美、聪慧", "f"),
    # 中性通用
    ("子", 3, "水", "才子、尊称、灵气", "n"),
    ("文", 4, "水", "文采、斯文、学识", "n"),
    ("安", 6, "土", "平安、安稳、泰然", "n"),
    ("家", 10, "木", "家庭、归属、温暖", "n"),
    ("乐", 15, "火", "快乐、喜乐、和乐", "n"),
    ("和", 8, "水", "和谐、温厚、平和", "n"),
    ("康", 11, "木", "健康、安宁、顺遂", "n"),
    ("然", 12, "金", "自然、从容、洒脱", "n"),
    ("明", 8, "火", "光明、贤明、清朗", "n"),
    ("嘉", 14, "木", "美好、嘉许、祥瑞", "n"),
    ("佳", 8, "木", "美好、优秀、上乘", "n"),
    ("慧", 15, "水", "聪慧、智慧、灵秀", "n"),
    ("颖", 16, "木", "聪颖、出众、灵慧", "n"),
    ("成", 6, "金", "成功、成就、圆满", "n"),
    # —— 常见姓名用字扩充（康熙笔画，用于测名/起名）——
    ("伟", 11, "土", "伟大、杰出、雄壮", "m"),
    ("强", 12, "木", "强壮、有力、上进", "m"),
    ("军", 9, "木", "军人、坚毅、担当", "m"),
    ("华", 14, "水", "华彩、光辉、繁盛", "m"),
    ("国", 11, "木", "国家、胸怀、正气", "m"),
    ("平", 5, "水", "平安、平稳、公正", "n"),
    ("刚", 10, "金", "刚强、正直、坚毅", "m"),
    ("勇", 9, "土", "勇敢、果决、胆识", "m"),
    ("磊", 15, "土", "光明磊落、坦荡", "m"),
    ("鹏", 19, "水", "大鹏、远大、腾飞", "m"),
    ("飞", 9, "水", "飞翔、高远、迅捷", "m"),
    ("健", 11, "木", "健康、强健、活力", "m"),
    ("涛", 18, "水", "波涛、气势、浩瀚", "m"),
    ("波", 9, "水", "波浪、灵动、起伏", "m"),
    ("超", 12, "金", "超越、出众、卓越", "m"),
    ("帅", 9, "金", "帅气、领袖、出众", "m"),
    ("龙", 16, "火", "龙、尊贵、腾达", "m"),
    ("坤", 8, "土", "大地、厚德、包容", "n"),
    ("锋", 15, "金", "锋芒、锐利、进取", "m"),
    ("杰", 12, "木", "杰出、豪杰、才干", "m"),
    ("旭", 6, "木", "旭日、光明、朝气", "m"),
    ("阳", 17, "火", "阳光、阳刚、光明", "m"),
    ("洋", 10, "水", "海洋、宽广、浩瀚", "m"),
    ("森", 12, "木", "森林、繁茂、生机", "m"),
    ("诚", 14, "金", "诚实、诚恳、信用", "m"),
    ("福", 14, "水", "福气、幸福、吉祥", "n"),
    ("海", 11, "水", "海洋、博大、包容", "m"),
    ("江", 7, "水", "江河、奔流、气度", "m"),
    ("山", 3, "土", "山峰、稳重、高远", "n"),
    ("东", 8, "木", "东方、希望、朝气", "m"),
    ("南", 9, "火", "南方、温暖、光明", "m"),
    ("光", 6, "火", "光明、荣耀、希望", "m"),
    ("天", 4, "火", "天空、宏大、高远", "n"),
    ("芳", 10, "木", "芬芳、美好、高洁", "f"),
    ("丽", 19, "火", "美丽、华丽、明艳", "f"),
    ("娜", 10, "火", "婀娜、柔美、优雅", "f"),
    ("娟", 10, "木", "娟秀、美好、清丽", "f"),
    ("秀", 7, "金", "秀丽、优秀、灵秀", "f"),
    ("英", 11, "木", "英华、杰出、飒爽", "f"),
    ("花", 10, "木", "花朵、美好、娇艳", "f"),
    ("梅", 11, "木", "梅花、坚韧、高洁", "f"),
    ("兰", 23, "木", "兰花、高洁、典雅", "f"),
    ("桂", 10, "木", "桂花、芬芳、祥瑞", "f"),
    ("凤", 14, "水", "凤凰、尊贵、祥瑞", "f"),
    ("玲", 10, "火", "玲珑、清脆、灵巧", "f"),
    ("珍", 10, "火", "珍贵、珍爱、美好", "f"),
    ("红", 9, "水", "红色、热烈、明艳", "f"),
    ("霞", 17, "水", "彩霞、绚烂、美好", "f"),
    ("萍", 14, "水", "浮萍、清雅、随和", "f"),
    ("燕", 16, "土", "燕子、灵巧、吉祥", "f"),
    ("月", 4, "木", "月亮、清雅、温柔", "f"),
    ("春", 9, "木", "春天、生机、温暖", "f"),
    ("秋", 9, "金", "秋天、成熟、丰实", "n"),
    ("梦", 16, "木", "梦想、浪漫、美好", "f"),
    # —— 二次扩充（更多常用字，康熙笔画）——
    ("恒", 9, "水", "恒心、持久、稳定", "n"),
    ("智", 12, "火", "智慧、聪慧、明理", "m"),
    ("信", 9, "金", "诚信、信用、可靠", "m"),
    ("仁", 4, "金", "仁爱、仁义、宽厚", "n"),
    ("鑫", 24, "金", "财富兴盛、多金", "m"),
    ("炎", 8, "火", "炎火、热烈、兴旺", "m"),
    ("岩", 8, "土", "岩石、坚定、稳固", "m"),
    ("泰", 9, "水", "安泰、稳重、通达", "n"),
    ("卓", 8, "火", "卓越、杰出、超群", "m"),
    ("晖", 13, "火", "光辉、照耀、明亮", "m"),
    ("皓", 12, "木", "皓洁、明亮、清朗", "m"),
    ("曦", 20, "火", "晨曦、光明、希望", "m"),
    ("岳", 8, "土", "山岳、高大、稳重", "m"),
    ("峻", 10, "土", "峻拔、高峻、坚毅", "m"),
    ("宸", 10, "金", "帝王居所、尊贵", "m"),
    ("元", 4, "木", "初始、根本、大气", "n"),
    ("启", 11, "木", "启发、开启、开端", "m"),
    ("初", 7, "金", "初始、初心、本真", "n"),
    ("宁", 14, "火", "安宁、平静、祥和", "n"),
    ("一", 1, "水", "唯一、专一、起始", "n"),
    ("薇", 16, "木", "蔷薇、美好、清雅", "f"),
    ("蓉", 16, "木", "芙蓉、美好、清丽", "f"),
    ("茜", 12, "木", "茜草、明艳、活泼", "f"),
    ("碧", 14, "水", "碧绿、清澈、纯净", "f"),
    ("翠", 14, "金", "翠绿、美玉、清雅", "f"),
    ("青", 8, "金", "青色、青春、生机", "f"),
    ("紫", 11, "金", "紫色、尊贵、优雅", "f"),
    ("丹", 4, "火", "丹红、赤诚、热烈", "f"),
    ("珊", 10, "金", "珊瑚、珍贵、美好", "f"),
    ("惠", 12, "水", "恩惠、贤惠、仁爱", "f"),
    ("雯", 12, "水", "云彩、文采、灵秀", "f"),
    ("婉", 11, "土", "温婉、柔美、娴雅", "f"),
    ("姿", 9, "金", "姿态、风韵、优雅", "f"),
    ("淑", 12, "水", "淑女、贤淑、温良", "f"),
    ("娴", 15, "土", "娴静、文雅、温婉", "f"),
    ("媛", 12, "土", "美女、名媛、美好", "f"),
    ("玫", 9, "金", "玫瑰、美好、娇艳", "f"),
    ("璇", 16, "火", "美玉、华美、祥瑞", "f"),
    ("瑾", 16, "火", "美玉、美德、高尚", "f"),
    ("瑜", 14, "金", "美玉、珍贵、美好", "f"),
]


# 常见姓氏康熙笔画（姓名学五格惯例）。表外姓氏会如实提示，不做猜测。
SURNAME_STROKES = {
    "王": 4, "李": 7, "张": 11, "刘": 15, "陈": 16, "杨": 13, "黄": 12, "赵": 14,
    "周": 8, "吴": 7, "徐": 10, "孙": 10, "胡": 9, "朱": 6, "高": 10, "林": 8,
    "何": 7, "郭": 10, "马": 10, "罗": 19, "梁": 11, "宋": 7, "郑": 14, "谢": 17,
    "韩": 17, "唐": 10, "冯": 12, "于": 3, "董": 12, "萧": 18, "程": 12, "曹": 11,
    "袁": 10, "邓": 14, "许": 11, "傅": 12, "沈": 7, "曾": 12, "彭": 12, "吕": 7,
    "苏": 20, "卢": 16, "蒋": 14, "蔡": 15, "贾": 13, "丁": 2, "魏": 17, "薛": 16,
    "叶": 15, "阎": 16, "余": 7, "潘": 15, "杜": 7, "戴": 17, "夏": 10, "钟": 17,
    "汪": 7, "田": 5, "任": 6, "姜": 9, "范": 8, "方": 4, "石": 5, "姚": 9,
    "谭": 19, "廖": 14, "邹": 13, "熊": 14, "金": 8, "陆": 16, "郝": 9, "孔": 4,
    "白": 5, "崔": 11, "康": 11, "毛": 4, "邱": 7, "秦": 10, "江": 6, "史": 5,
    "顾": 21, "侯": 9, "邵": 7, "孟": 8, "龙": 16, "万": 15, "段": 9, "雷": 13,
    "钱": 16, "汤": 12, "尹": 4, "黎": 15, "易": 8, "常": 11, "武": 8, "乔": 12,
    "贺": 12, "赖": 16, "龚": 22, "文": 4, "欧阳": 23, "司马": 15, "上官": 11,
}


def _char_strokes(name: str) -> int:
    """单字或复姓的康熙笔画和（表外字笔画按 1 计，需前端/说明提示）。"""
    total = 0
    for ch in name:
        total += next((c[1] for c in CHARS if c[0] == ch), 0)
    return total


def _surname_strokes(surname: str) -> int:
    """姓氏康熙笔画；表外姓氏抛出异常以如实提示。"""
    if surname in SURNAME_STROKES:
        return SURNAME_STROKES[surname]
    # 复姓未命中时，尝试按单字查表求和
    if len(surname) == 2:
        try:
            return SURNAME_STROKES[surname[0]] + SURNAME_STROKES[surname[1]]
        except KeyError:
            pass
    raise ValueError(f"姓氏「{surname}」暂不在姓氏字库中，请换一个常见姓氏或改问其他事项")


def _suggest_wuxing(req: NamingRequest) -> list:
    """建议补益的五行：有八字则取缺失五行（参考），否则全部五行。"""
    if req.bazi:
        try:
            bz = compute_bazi(req.bazi)
            return bz["missing_wuxing"] or ["金", "木", "水", "火", "土"]
        except Exception:
            pass
    return ["金", "木", "水", "火", "土"]


def _wuge(surname_strokes: int, given_strokes: list) -> dict:
    """五格数理：天格/人格/地格/外格/总格。"""
    tian = surname_strokes + 1
    ren = surname_strokes + given_strokes[0]
    di = sum(given_strokes) if len(given_strokes) == 2 else given_strokes[0] + 1
    zong = surname_strokes + sum(given_strokes)
    wai = zong - ren + 1 if len(given_strokes) == 2 else 2
    return {"天格": tian, "人格": ren, "地格": di, "外格": wai, "总格": zong}


def compute_naming(req: NamingRequest) -> dict:
    surname = req.surname.strip()
    if not surname:
        raise ValueError("请填写姓氏")
    lang = getattr(req, "lang", "zh")
    if lang == "en" or (lang == "zh" and _detect_lang(surname) == "english"):
        return _naming_foreign(req, ENGLISH_NAMES)
    if lang == "ja" or (lang == "zh" and _detect_lang(surname) == "japanese_kana"):
        return _naming_foreign(req, JAPANESE_NAMES)
    surname_strokes = _surname_strokes(surname)
    target = _suggest_wuxing(req)

    gender_set = {"n"}
    gender_set.add("m" if req.gender == "男" else "f")

    # 按性别 + 五行 + 偏好筛选可用字
    pool = [c for c in CHARS if c[4] in gender_set and c[2] in target]
    if not pool:
        pool = [c for c in CHARS if c[4] in gender_set]

    pref = (req.preference or "").strip()
    if pref:
        matched = [c for c in pool if pref in c[3]]
        # 偏好命中至少 2 个字才应用过滤，否则保留完整字库，偏好交由大模型综合
        if len(matched) >= 2:
            pool = matched

    candidates = []
    seen = set()
    # 双字名：取前 12 个字两两组合
    limited = pool[:12]
    for a in limited:
        for b in limited:
            if a[0] == b[0]:
                continue
            chars = [a, b]
            given = "".join(c[0] for c in chars)
            full = surname + given
            if full in seen:
                continue
            seen.add(full)
            candidates.append({
                "full_name": full,
                "given_name": given,
                "chars": [{"char": c[0], "strokes": c[1], "wuxing": c[2], "meaning": c[3]} for c in chars],
                "wuge": _wuge(surname_strokes, [c[1] for c in chars]),
                "meaning": "；".join(c[3] for c in chars),
            })
            if len(candidates) >= 16:
                break
        if len(candidates) >= 16:
            break

    return {
        "surname": surname,
        "surname_strokes": surname_strokes,
        "gender": req.gender,
        "suggest_wuxing": target,
        "preference": pref,
        "candidates": candidates,
    }


# 名字用字索引（按单字快速查找笔画/五行/寓意）
_CHAR_INDEX = {c[0]: {"strokes": c[1], "wuxing": c[2], "meaning": c[3]} for c in CHARS}


def _wuxing_missing(chars_wuxing: list) -> list:
    """统计姓名用字五行的缺失（补益参考）。"""
    counts = {w: chars_wuxing.count(w) for w in ("金", "木", "水", "火", "土")}
    return [w for w, c in counts.items() if c == 0]


def compute_name_fortune(name: str) -> dict:
    """测名：中文/日文汉字算五格数理，英文名算毕达哥拉斯灵数。"""
    name = (name or "").strip()
    if not name:
        raise ValueError("请输入姓名")
    if _detect_lang(name) == "english":
        return _name_fortune_english(name)
    if not (2 <= len(name) <= 4):
        raise ValueError("请输入 2~4 个字的姓名")

    # 识别复姓（欧阳 / 司马 / 上官）
    surname = name[0]
    if len(name) >= 3 and name[:2] in SURNAME_STROKES:
        surname = name[:2]
    given = name[len(surname):]
    if not given:
        raise ValueError("请同时填写名字部分")

    surname_strokes = _surname_strokes(surname)

    chars = []
    unknown = []
    for ch in given:
        info = _CHAR_INDEX.get(ch)
        if info:
            chars.append({"char": ch, "strokes": info["strokes"], "wuxing": info["wuxing"], "meaning": info["meaning"]})
        else:
            unknown.append(ch)
            chars.append({"char": ch, "strokes": None, "wuxing": None, "meaning": None})

    wuge = None
    if not unknown:
        wuge = _wuge(surname_strokes, [c["strokes"] for c in chars])

    known_wuxing = [c["wuxing"] for c in chars if c["wuxing"]]
    return {
        "name": name,
        "surname": surname,
        "given": given,
        "surname_strokes": surname_strokes,
        "chars": chars,
        "unknown_chars": unknown,
        "wuge": wuge,
        "wuxing_missing": _wuxing_missing(known_wuxing) if not unknown else None,
    }


# ---------- 多语言支持（英文名 / 日文名） ----------

# 常见英文名（含中文音译与含义）
ENGLISH_NAMES = {
    "男": [
        ("James", "詹姆斯 · 取代者"), ("John", "约翰 · 神是仁慈的"),
        ("Michael", "迈克尔 · 像神的人"), ("David", "大卫 · 被爱的"),
        ("William", "威廉 · 坚定的守护者"), ("Daniel", "丹尼尔 · 神是我的审判者"),
        ("Ethan", "伊桑 · 坚定稳固"), ("Noah", "诺亚 · 安息安慰"),
        ("Liam", "利亚姆 · 坚强守护"), ("Lucas", "卢卡斯 · 光明"),
        ("Henry", "亨利 · 家族统治者"), ("Oliver", "奥利弗 · 和平橄榄树"),
        ("Alexander", "亚历山大 · 人类守护者"), ("Leo", "里奥 · 狮子·勇者"),
    ],
    "女": [
        ("Emma", "艾玛 · 宇宙全能"), ("Olivia", "奥利维亚 · 橄榄树·和平"),
        ("Sophia", "索菲亚 · 智慧"), ("Isabella", "伊莎贝拉 · 献给神"),
        ("Mia", "米娅 · 我的挚爱"), ("Charlotte", "夏洛特 · 自由人"),
        ("Amelia", "阿米莉亚 · 勤劳"), ("Evelyn", "伊芙琳 · 生命美好"),
        ("Abigail", "阿比盖尔 · 父亲的喜悦"), ("Emily", "艾米丽 · 勤劳"),
        ("Elizabeth", "伊丽莎白 · 神的誓言"), ("Grace", "格蕾丝 · 优雅恩典"),
        ("Lily", "莉莉 · 百合·纯洁"), ("Chloe", "克洛伊 · 青春的"),
    ],
}

# 常见日文名（含中文含义）
JAPANESE_NAMES = {
    "男": [
        ("翔", "飞翔、高远"), ("大輝", "光辉、耀眼"), ("健太", "健康、强壮"),
        ("拓海", "开拓海洋、进取"), ("蓮", "莲花、纯洁"), ("悠人", "悠然、从容"),
        ("颯太", "飒爽、爽朗"), ("湊", "水汇聚处、包容"), ("樹", "树、成长"),
        ("陽翔", "向阳飞翔"), ("大和", "和谐、大气"), ("陸", "陆地、踏实"),
    ],
    "女": [
        ("陽葵", "向阳的葵花"), ("結衣", "结缘的衣裳"), ("凛", "凛然、清冷高贵"),
        ("陽菜", "向阳的菜、温暖"), ("結愛", "结缘的爱"), ("さくら", "樱花、烂漫"),
        ("芽依", "萌芽、希望"), ("美月", "美丽的月亮"), ("葵", "葵花、向阳"),
        ("紬", "丝绸、温婉"), ("澪", "水脉、清澈"), ("莉子", "茉莉、清香"),
    ],
}


def _detect_lang(s: str) -> str:
    """检测字符串类型：english / japanese_kana / cjk（中文或日文汉字）。"""
    has_latin = any(("a" <= ch <= "z") or ("A" <= ch <= "Z") for ch in s)
    has_kana = any("぀" <= ch <= "ヿ" for ch in s)
    has_cjk = any("一" <= ch <= "鿿" for ch in s)
    if has_latin and not has_cjk and not has_kana:
        return "english"
    if has_kana:
        return "japanese_kana"
    return "cjk"


def _name_fortune_english(name: str) -> dict:
    """英文名测名：毕达哥拉斯灵数。"""
    from app.divination import numerology

    letters = [numerology.LETTER_NUM[c] for c in name.upper() if c in numerology.LETTER_NUM]
    if not letters:
        raise ValueError("请输入英文名（字母）")
    num = numerology._reduce(sum(letters))
    return {
        "name": name,
        "type": "english",
        "number": num,
        "meaning": numerology.MEANINGS.get(num, "灵数"),
    }


def _naming_foreign(req, name_map: dict) -> dict:
    """英文/日文起名：从名字库返回候选。"""
    key = "男" if req.gender == "男" else "女"
    names = name_map.get(key, [])
    pref = (req.preference or "").strip()
    candidates = [{"name": n, "meaning": m} for n, m in names]
    if pref:
        matched = [c for c in candidates if pref in c["name"] or pref in c["meaning"]]
        if matched:
            candidates = matched
    return {
        "surname": req.surname,
        "gender": req.gender,
        "type": "foreign",
        "preference": pref,
        "candidates": candidates,
    }
