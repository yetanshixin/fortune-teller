"""卢恩符文（Elder Futhark，24 符文）抽取。"""
import random

from app.schemas import RuneRequest

# 24 符文：名称、字母、含义(正)、含义(逆/或标记为无逆位)
RUNES = [
    ("Fehu", "ᚠ", "财富、富足、成功、能量", "损失、贪婪、计划受挫", True),
    ("Uruz", "ᚢ", "力量、健康、勇气、行动", "虚弱、错失、固执", True),
    ("Thurisaz", "ᚦ", "保护、突破、反击、边界", "威胁、冲动、防御过度", True),
    ("Ansuz", "ᚨ", "沟通、灵感、智慧、信息", "误解、欺骗、沟通不畅", True),
    ("Raidho", "ᚱ", "旅程、进步、秩序、节奏", "延误、停滞、迷失方向", True),
    ("Kenaz", "ᚲ", "启示、创造力、清晰、知识", "迷雾、灵感枯竭、误解", True),
    ("Gebo", "ᚷ", "礼物、合作、平衡、契约", None, False),
    ("Wunjo", "ᚹ", "喜悦、满足、和谐、成就", "悲伤、冲突、期望落空", True),
    ("Hagalaz", "ᚺ", "突然的破坏、考验、彻底转变", None, False),
    ("Nauthiz", "ᚾ", "克制、耐心、逆境中坚持", "焦虑、匮乏、自我限制", True),
    ("Isa", "ᛁ", "静止、冻结、暂停、积蓄", None, False),
    ("Jera", "ᛃ", "丰收、回报、循环、时机成熟", None, False),
    ("Eihwaz", "ᛇ", "忍耐、转变、保护、韧性", None, False),
    ("Perthro", "ᛈ", "命运、机遇、未知、偶然", "停滞、被动的命运、逃避", True),
    ("Algiz", "ᛉ", "保护、守护、直觉、神圣", "脆弱、被忽视、防御不足", True),
    ("Sowilo", "ᛊ", "成功、活力、光明、胜利", None, False),
    ("Tiwaz", "ᛏ", "正义、胜利、勇气、意志", "不公、意志动摇、受挫", True),
    ("Berkano", "ᛒ", "新生、成长、家庭、孕育", "停滞、焦虑、成长受阻", True),
    ("Ehwaz", "ᛖ", "合作、进展、信任、协作", "背叛、停滞、不协调", True),
    ("Mannaz", "ᛗ", "自我、社会、互助、人性", "孤立、自私、自我怀疑", True),
    ("Laguz", "ᛚ", "流动、直觉、疗愈、情感", "迷失、情绪泛滥、逃避", True),
    ("Ingwaz", "ᛜ", "孕育、潜力、完成、内在力量", None, False),
    ("Dagaz", "ᛞ", "突破、觉醒、光明、转机", None, False),
    ("Othala", "ᛟ", "家园、遗产、传承、归属", "失去、束缚、固守过去", True),
]


def draw_runes(count: int = 3) -> dict:
    """随机抽取符文，可带正逆位。"""
    chosen = random.sample(RUNES, min(count, len(RUNES)))
    result = []
    for name, glyph, upright, reversed_, reversible in chosen:
        is_reversed = reversible and random.random() < 0.5
        result.append({
            "name": name,
            "glyph": glyph,
            "reversed": is_reversed,
            "meaning": (reversed_ if is_reversed else upright),
        })
    return {"count": len(result), "runes": result}
