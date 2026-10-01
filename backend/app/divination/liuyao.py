"""六爻纳甲装卦（摇卦结果 → 本卦/变卦/纳甲/六亲/世应）。"""
from app.divination.bagua import (
    gong_of_hexagram,
    hexagram_from_lines,
    line_name,
    liuqin,
    najia_of_hexagram,
)
from app.schemas import LiuYaoRequest

# 摇卦数 → (爻性, 是否动, 名称)
_YAO = {
    6: (0, True, "老阴 ×（动）"),
    7: (1, False, "少阳 —"),
    8: (0, False, "少阴 - -"),
    9: (1, True, "老阳 ○（动）"),
}


def compute_liuyao(req: LiuYaoRequest) -> dict:
    lines = list(req.lines)  # 自初爻到上爻
    ben_lines = [_YAO[v][0] for v in lines]
    bian_lines = [b ^ 1 if _YAO[v][1] else b for b, v in zip(ben_lines, lines)]

    ben = hexagram_from_lines(ben_lines)
    bian = hexagram_from_lines(bian_lines)
    gong_name, gong_wuxing, shi, ying, pos = gong_of_hexagram(ben["seq"])
    zh_is = najia_of_hexagram(ben["lower"], ben["upper"])

    yao_list = []
    for i in range(6):
        v = lines[i]
        yin, moving, label = _YAO[v]
        yao_list.append({
            "pos": i + 1,
            "pos_name": line_name(i + 1),
            "value": v,
            "yin_yang": "阳" if yin else "阴",
            "label": label,
            "moving": moving,
            "najia_zhi": zh_is[i],
            "liuqin": liuqin(zh_is[i], gong_wuxing),
            "shi_ying": "世" if (i + 1) == shi else ("应" if (i + 1) == ying else ""),
        })

    moving_positions = [i + 1 for i in range(6) if _YAO[lines[i]][1]]

    return {
        "ben": ben,
        "bian": bian,
        "gong": gong_name,
        "gong_wuxing": gong_wuxing,
        "shi_yao": shi,
        "ying_yao": ying,
        "yao": yao_list,
        "moving_positions": moving_positions,
        "changed": bool(moving_positions),
    }
