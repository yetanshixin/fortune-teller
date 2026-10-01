"""FastAPI 入口：提供聊天 API、术数排盘接口，并托管前端静态资源。"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app import persona
from app.config import ALLOWED_MODELS, HOST, PORT
from app.divination import bazi, dream, huangli, liuyao, meihua, naming, numerology, runes, tarot
from app.schemas import (
    BaziRequest,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CompanyNamingRequest,
    DreamRequest,
    HuangLiRequest,
    LiuYaoRequest,
    MeiHuaRequest,
    NameFortuneRequest,
    NamingRequest,
    NumerologyRequest,
    RuneRequest,
    TarotRequest,
)
from app.services import deepseek

BASE_DIR = Path(__file__).resolve().parents[2]  # 项目根目录（fortune-teller）
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="AI 算命先生", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "model": deepseek.DEEPSEEK_MODEL,
        "models": ALLOWED_MODELS,
    }


def _build_messages(req: ChatRequest) -> list:
    """注入算命先生系统提示词，并替换掉客户端自带的 system 消息。"""
    sys_prompt = persona.build_system_prompt()
    return [ChatMessage(role="system", content=sys_prompt)] + [
        m for m in req.messages if m.role != "system"
    ]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = _build_messages(req)

    if req.stream:
        async def event_stream():
            try:
                async for token in deepseek.chat_completion_stream(
                    messages,
                    req.temperature,
                    req.max_tokens,
                    model=req.model,
                    api_key=req.api_key,
                ):
                    data = json.dumps({"delta": token}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as exc:  # noqa: BLE001
                data = json.dumps({"error": str(exc)}, ensure_ascii=False)
                yield f"data: {data}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        reply = await deepseek.chat_completion(
            messages,
            req.temperature,
            req.max_tokens,
            model=req.model,
            api_key=req.api_key,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}")

    return ChatResponse(reply=reply, model=deepseek._resolve_model(req.model))


# ---------- 术数排盘接口（确定性算法，返回结构化结果） ----------

@app.post("/api/divination/bazi")
async def div_bazi(req: BaziRequest):
    return bazi.compute_bazi(req)


@app.post("/api/divination/liuyao")
async def div_liuyao(req: LiuYaoRequest):
    if any(v not in (6, 7, 8, 9) for v in req.lines):
        raise HTTPException(status_code=400, detail="摇卦结果须为 6/7/8/9（老阴/少阳/少阴/老阳）")
    return liuyao.compute_liuyao(req)


@app.post("/api/divination/meihua")
async def div_meihua(req: MeiHuaRequest):
    try:
        return meihua.compute_meihua(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/divination/tarot")
async def div_tarot(req: TarotRequest):
    return tarot.draw_tarot(req.spread)


@app.post("/api/divination/runes")
async def div_runes(req: RuneRequest):
    return runes.draw_runes(req.count)


@app.post("/api/divination/numerology")
async def div_numerology(req: NumerologyRequest):
    return numerology.compute_numerology(req)


@app.post("/api/divination/huangli")
async def div_huangli(req: HuangLiRequest):
    return huangli.compute_huangli(req)


@app.post("/api/divination/dream")
async def div_dream(req: DreamRequest):
    return dream.compute_dream(req)


@app.post("/api/divination/naming")
async def div_naming(req: NamingRequest):
    try:
        return naming.compute_naming(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/divination/name_fortune")
async def div_name_fortune(req: NameFortuneRequest):
    try:
        return naming.compute_name_fortune(req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/divination/company_naming")
async def div_company_naming(req: CompanyNamingRequest):
    try:
        return naming.compute_company_naming(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# 托管前端静态资源（放在 API 路由之后，避免拦截 /api）
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
