"""塔罗牌（78 张，韦特塔罗）抽牌与牌阵。"""
import random

from app.schemas import TarotRequest

# 大阿尔卡纳 22 张：名称、正位、逆位
MAJOR = [
    ("愚者", "新的开始、冒险、纯真、自由", "鲁莽、犹豫、漫无目的、风险"),
    ("魔术师", "创造力、能力、意志、行动力", "欺骗、滥用才能、计划落空"),
    ("女祭司", "直觉、潜意识、智慧、神秘", "忽视直觉、隐藏信息、表里不一"),
    ("皇后", "丰饶、母性、滋养、富足", "依赖、过度、缺乏安全感"),
    ("皇帝", "权威、秩序、稳定、领导力", "专制、僵化、失控"),
    ("教皇", "传统、信仰、导师、道德准则", "叛逆、教条、误导"),
    ("恋人", "爱情、结合、和谐、重要抉择", "不和、诱惑、错误选择"),
    ("战车", "意志、胜利、掌控、勇往直前", "失控、受阻、方向迷失"),
    ("力量", "勇气、耐心、以柔克刚、自信", "软弱、自我怀疑、压抑"),
    ("隐士", "内省、独处、求索、智慧", "孤僻、逃避、自我封闭"),
    ("命运之轮", "转机、命运、循环、好运降临", "厄运、停滞、世事无常"),
    ("正义", "公正、因果、平衡、真相", "不公、偏袒、逃避责任"),
    ("倒吊人", "牺牲、换位思考、暂停、顿悟", "无谓牺牲、僵持、拖延"),
    ("死神", "结束、重生、蜕变、放下", "抗拒改变、停滞、恐惧结束"),
    ("节制", "平衡、调和、耐心、中庸之道", "失衡、过度、急躁"),
    ("恶魔", "欲望、束缚、诱惑、执念", "挣脱、觉醒、摆脱依赖"),
    ("高塔", "突变、崩塌、真相揭露、剧变", "推迟的灾变、侥幸、逃避"),
    ("星星", "希望、疗愈、灵感、宁静", "失望、信心不足、迷惘"),
    ("月亮", "不安、幻觉、潜意识、迷惑", "真相浮现、走出迷茫、平复"),
    ("太阳", "成功、喜悦、活力、光明", "短暂的成功、过度乐观、黯淡"),
    ("审判", "觉醒、召唤、重生、宽恕", "自我怀疑、错失、无法释怀"),
    ("世界", "圆满、完成、整合、成就", "未竟、停滞、缺乏收尾"),
]

# 小阿尔卡纳：组别(名称/元素/主题)，数字牌关键词模板，宫廷牌角色
MINOR_SUITS = [
    ("权杖", "火", "行动 · 热情 · 事业", "活力、行动、开创", "冲动、拖延、精力分散"),
    ("圣杯", "水", "情感 · 关系 · 直觉", "情感流动、关系、滋养", "情绪化、幻灭、付出失衡"),
    ("宝剑", "风", "思想 · 冲突 · 挑战", "理性、决断、真相", "焦虑、纷争、言语伤害"),
    ("星币", "土", "物质 · 金钱 · 稳定", "务实、收获、稳定", "守财、物质焦虑、停滞"),
]
MINOR_NUMBERS = ["王牌", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
MINOR_COURT = [
    ("侍从", "学习、消息、潜力", "不成熟、轻率、消息延迟"),
    ("骑士", "行动、追求、冲劲", "冒进、鲁莽、失衡"),
    ("王后", "成熟、内化、包容", "过度、情绪绑架、失衡"),
    ("国王", "掌控、权威、成就", "独断、僵化、滥用权力"),
]
# 数字牌 1~10 的通用倾向（结合组别主题解读）
NUMBER_MEANING = [
    "新的开始与机会",
    "平衡、抉择与联合",
    "成长、合作与初步成果",
    "稳定、巩固与休整",
    "冲突、挑战与失去",
    "和谐、恢复与分享",
    "反思、坚持与评估",
    "行动、变化与提速",
    "成果、接近圆满与满足",
    "完成、顶峰与新的循环",
]

# 牌阵位置定义
SPREADS = {
    "single": ["整体情况"],
    "three": ["过去", "现在", "未来"],
    "celtic": ["当下处境", "挑战/障碍", "潜意识根基", "过去的根源", "目标/理想", "不久的将来",
               "自身态度", "外部环境", "希望与恐惧", "最终结果"],
}


def _build_deck():
    deck = []
    for name, upright, reversed_ in MAJOR:
        deck.append({"name": name, "arcana": "大阿尔卡纳", "upright": upright, "reversed": reversed_})
    for suit, element, theme, upright_theme, reversed_theme in MINOR_SUITS:
        for i, num in enumerate(MINOR_NUMBERS):
            deck.append({
                "name": f"{suit}{num}",
                "arcana": "小阿尔卡纳",
                "suit": suit, "element": element,
                "upright": f"{upright_theme}；{NUMBER_MEANING[i]}",
                "reversed": f"{reversed_theme}；{NUMBER_MEANING[i]}受阻或过度",
            })
        for role, u, r in MINOR_COURT:
            deck.append({
                "name": f"{suit}{role}",
                "arcana": "小阿尔卡纳",
                "suit": suit, "element": element,
                "upright": f"{role}：{u}",
                "reversed": f"{role}：{r}",
            })
    return deck


DECK = _build_deck()


def draw_tarot(spread: str = "three") -> dict:
    """抽牌：随机洗牌，返回牌阵各位置的牌（含正逆位）。"""
    positions = SPREADS.get(spread, SPREADS["three"])
    cards = random.sample(DECK, len(positions))
    result = []
    for pos, card in zip(positions, cards):
        reversed_ = random.random() < 0.5
        result.append({
            "position": pos,
            "name": card["name"],
            "arcana": card.get("arcana", "小阿尔卡纳"),
            "element": card.get("element", ""),
            "reversed": reversed_,
            "meaning": card["reversed"] if reversed_ else card["upright"],
        })
    return {"spread": spread, "cards": result}
