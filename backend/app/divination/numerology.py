"""生命灵数（毕达哥拉斯灵数体系）。"""
from app.schemas import NumerologyRequest

# 灵数含义（含主数 11 / 22 / 33）
MEANINGS = {
    1: "开创者：独立、自信、领导力强，勇于开拓新局。需注意独断与急躁。",
    2: "协调者：温和、敏锐、善解人意，擅长合作与平衡。需避免优柔寡断与过度依赖。",
    3: "表达者：乐观、创意十足、社交活跃，富有感染力。需注意专注力与浮夸。",
    4: "建设者：务实、勤勉、重秩序与承诺，可靠稳妥。需避免固执与僵化。",
    5: "探索者：自由、多变、充满活力，追求体验与冒险。需注意缺乏耐心与贪多。",
    6: "守护者：重责任、关爱、家庭与和谐，乐于付出。需避免过度操心与牺牲自我。",
    7: "思考者：内省、灵性、聪慧、爱分析，追求真知。需避免孤僻与过度怀疑。",
    8: "成就者：追求权力、财富与效率，有商业头脑与执行力。需注意功利与过度掌控。",
    9: "人道者：博爱、理想、宽容，志在奉献与成全。需避免不切实际与过度牺牲。",
    11: "灵性启蒙者（主数）：直觉敏锐、富有洞见与感召力。需平衡敏感与落地。",
    22: "大师建造者（主数）：愿景宏大、务实而有远见，能成大事。需避免压力过大与好高骛远。",
    33: "大师导师（主数）：无私之爱、奉献与教化，胸怀博大。需注意边界与自我照顾。",
}

# 毕达哥拉斯字母数（英文姓名灵数）
LETTER_NUM = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}


def _reduce(n: int) -> int:
    """把数字化为 1~9，或保留主数 11/22/33。"""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def _name_number(name: str) -> int:
    letters = [LETTER_NUM[c] for c in name.upper() if c in LETTER_NUM]
    if not letters:
        return 0
    return _reduce(sum(letters))


def compute_numerology(req: NumerologyRequest) -> dict:
    life_path = _reduce(
        sum(int(d) for d in f"{req.year:04d}{req.month:02d}{req.day:02d}")
    )
    result = {
        "life_path": life_path,
        "life_path_meaning": MEANINGS.get(life_path, "灵数"),
        "birthday": f"{req.year}-{req.month:02d}-{req.day:02d}",
    }
    if req.name:
        n = _name_number(req.name)
        result["name_number"] = n
        result["name_number_meaning"] = MEANINGS.get(n, "姓名灵数") if n else None
    return result
