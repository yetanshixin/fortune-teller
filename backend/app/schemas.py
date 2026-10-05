"""请求 / 响应的数据模型。"""
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None        # 指定模型，非法值回退默认
    api_key: Optional[str] = None      # 自定义 Key，无效回退默认 Key
    stream: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class ChatResponse(BaseModel):
    reply: str
    model: str


# ---------- 术数测算请求模型 ----------

class BaziRequest(BaseModel):
    """八字排盘请求。calendar: solar=公历 / lunar=农历。"""
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    gender: Literal["男", "女"] = "男"
    calendar: Literal["solar", "lunar"] = "solar"


class LiuYaoRequest(BaseModel):
    """六爻请求。lines 为 6 次摇卦结果，从初爻到上爻，每项为 6/7/8/9。"""
    lines: List[int] = Field(..., min_length=6, max_length=6)


class MeiHuaRequest(BaseModel):
    """梅花易数请求。type: number=数字起卦 / time=时间起卦 / word=测字。"""
    type: Literal["number", "time", "word"] = "number"
    numbers: Optional[List[int]] = None   # 数字起卦（1~3 个数字）
    time: Optional[str] = None            # 时间起卦 "YYYY-MM-DD HH:MM"
    word: Optional[str] = None            # 测字（单个或多个汉字）


class TarotRequest(BaseModel):
    """塔罗抽牌。spread: single=单张 / three=三牌阵(过去现在未来) / celtic=凯尔特十字(10张)。"""
    spread: Literal["single", "three", "celtic"] = "three"


class NumerologyRequest(BaseModel):
    """生命灵数。name 为中文或英文姓名，仅用于姓名灵数（英文）。"""
    year: int
    month: int
    day: int
    name: Optional[str] = None


class HuangLiRequest(BaseModel):
    """黄历/择日查询。matter 为事项（用于宜忌解读，可选）。"""
    year: int
    month: int
    day: int
    matter: Optional[str] = None


class DreamRequest(BaseModel):
    """解梦请求：用户描述或关键词。"""
    text: str = Field(..., min_length=1, max_length=500)


class NamingRequest(BaseModel):
    """起名请求。surname 必填；lang 语言（zh 中文/en 英文/ja 日文）；bazi 生辰（可选）；old_name 旧名（改名用，可选）；gender 风格倾向。"""
    surname: str = Field(..., min_length=1, max_length=20)
    gender: Literal["男", "女"] = "男"
    lang: Literal["zh", "en", "ja"] = "zh"
    bazi: Optional[BaziRequest] = None
    old_name: Optional[str] = None    # 改名：原有名字（可选）
    preference: Optional[str] = None   # 期望寓意/风格，如「温婉」「大气」


class NameFortuneRequest(BaseModel):
    """测名请求：输入完整姓名（中文/日文汉字或英文名）。"""
    name: str = Field(..., min_length=1, max_length=40)


class CompanyNamingRequest(BaseModel):
    """公司取名请求。industry 行业；lang 语言（zh/en/ja）；preference 期望寓意（可选）；length 商号字数。"""
    industry: str = Field(..., min_length=1, max_length=20)
    lang: Literal["zh", "en", "ja"] = "zh"
    preference: Optional[str] = None
    length: int = Field(default=2, ge=2, le=4)


class HeHunRequest(BaseModel):
    """合婚请求：男女双方生辰。"""
    male: BaziRequest
    female: BaziRequest


class ChouQianRequest(BaseModel):
    """抽签请求（随机抽一支签）。"""
    pass


class ShuZiRequest(BaseModel):
    """数字测吉凶请求：手机号/车牌号等数字串。"""
    number: str = Field(..., min_length=1, max_length=20)
