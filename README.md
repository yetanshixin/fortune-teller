# 玄机先生 · AI 算命先生

一个前后端分离的 AI 算命先生项目。AI 扮演一位精通**八字、六爻、梅花易数、塔罗、卢恩符文、生命灵数、黄历择日、起名、解梦**等中西方术数的算命先生，提供问感情、问财运、测事、起名、择日、解梦、做决策、看运势、心理安抚等服务。

核心原则：**真把式，绝不做江湖骗子**——所有「排盘」都由后端**确定性算法**精确计算，大模型只负责基于真实排盘数据做自然语言解读，绝不凭空编造干支、卦象。

---

## 功能特性

- **前端**：原生 HTML / CSS / JavaScript，使用 **axios** 对接后端；玄学主题（深色墨底 + 金色点缀），移动端适配；支持 SSE 流式输出、Markdown 渲染、多会话历史、深色/浅色主题。
- **后端**：使用 **uv** 管理 Python 项目，基于 **FastAPI**，对接 **DeepSeek** 大模型（`deepseek-flash` 默认，关闭思考模式）。
- **术数排盘引擎**（真实算法）：
  - 八字四柱、五行、十神、纳音、大运（基于 [`lunar-python`](https://github.com/6tail/lunar-python) 历法内核）
  - 六爻纳甲装卦（本卦/变卦/六亲/世应）
  - 梅花易数（数字/时间/测字起卦）
  - 塔罗牌（78 张、多牌阵）、卢恩符文（24 符文）
  - 生命灵数、黄历择日（宜忌/建除/冲煞/吉神方位）
  - 解梦词典、起名（五行补益 + 五格数理 + 字义）、测名（姓名五格数理吉凶）、测字（拆字断卦）
- **设置**：切换大模型（`deepseek-flash` / `deepseek-v4-pro`）、自定义 API Key（无效自动回退默认 Key）。
- **对话数据**：全部存浏览器 localStorage。

## 目录结构

```
fortune-teller/
├── backend/                 # FastAPI 后端（uv 管理）
│   ├── pyproject.toml
│   ├── .python-version
│   ├── .env                 # 本地环境配置（含默认 Key，已 gitignore）
│   ├── .env.example
│   ├── requirements.txt     # uv 导出
│   └── app/
│       ├── main.py          # 入口：/api/chat、/api/health、术数接口、托管前端
│       ├── config.py        # 配置（模型白名单、默认 Key 回退）
│       ├── schemas.py       # 请求/响应模型
│       ├── persona.py       # 算命先生系统提示词
│       ├── services/deepseek.py  # 大模型调用（流式/非流式、模型/Key 切换）
│       └── divination/      # 术数排盘引擎（真实算法）
├── frontend/                # 前端静态资源
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── vendor/          # 本地 axios / marked / DOMPurify
├── render.yaml              # Render 部署配置
└── README.md
```

## 快速开始

### 1. 安装 uv（如未安装）

```bash
pip install uv
```

### 2. 安装后端依赖并启动

```bash
cd backend
uv sync                                  # 创建虚拟环境并安装依赖
uv run uvicorn app.main:app --reload --port 8000
```

浏览器访问 `http://localhost:8000` 即可（前端已由 FastAPI 一并托管）。

> 也可直接双击打开 `frontend/index.html`（`file://` 协议），前端会自动把请求指向 `http://localhost:8000`，后端已开启 CORS。

## 配置说明

后端配置从 `backend/.env` 读取（缺省值见 `app/config.py`）：

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 默认 API Key | 见 `.env` |
| `DEEPSEEK_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 默认模型 | `deepseek-flash` |
| `HOST` / `PORT` | 监听地址 | `0.0.0.0` / `8000` |

可选模型：`deepseek-flash`、`deepseek-v4-pro`（前端设置里可切换）。

## API 接口

### `GET /api/health`
健康检查，返回状态、默认模型与可选模型列表。

### `POST /api/chat`
对话接口（流式 SSE / 非流式）。请求体：

```json
{
  "messages": [{ "role": "user", "content": "帮我看看今年的运势" }],
  "model": "deepseek-flash",
  "api_key": "",
  "stream": true
}
```

### 术数排盘接口（均为 POST，返回确定性排盘结果）

| 接口 | 说明 |
| --- | --- |
| `/api/divination/bazi` | 八字四柱排盘 |
| `/api/divination/liuyao` | 六爻纳甲装卦 |
| `/api/divination/meihua` | 梅花易数起卦 |
| `/api/divination/tarot` | 塔罗抽牌 |
| `/api/divination/runes` | 卢恩符文抽取 |
| `/api/divination/numerology` | 生命灵数 |
| `/api/divination/huangli` | 黄历/择日查询 |
| `/api/divination/dream` | 解梦关键词匹配 |
| `/api/divination/naming` | 起名（五行补益 + 五格） |
| `/api/divination/name_fortune` | 测名（姓名五格数理 + 五行吉凶） |

## 部署到 Render

### 方式一：Blueprint（推荐）

1. 把本项目推送到 GitHub 仓库。
2. 在 Render 新建 **Blueprint**，选择仓库，Render 会读取根目录的 `render.yaml` 自动创建 Web 服务。
3. 确认环境变量 `DEEPSEEK_API_KEY` 已配置（`render.yaml` 中已写入默认值，可在 Render 面板覆盖）。

### 方式二：手动创建 Web Service

1. Render 新建 **Web Service**，连接仓库。
2. 配置：
   - **Root Directory**：`backend`
   - **Runtime**：Python 3
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. 添加环境变量 `DEEPSEEK_API_KEY`（值为你的 Key）。

## 注意事项

- `backend/.env` 中的 API Key 属于敏感信息，已被 `.gitignore` 忽略，请勿提交到版本库。
- 后端通过请求体 `"thinking": {"type": "disabled"}` **关闭模型思考模式**（回复更直接、无思考延迟）。
- 前端依赖（axios/marked/DOMPurify）已本地化，无需联网加载 CDN。
- 关于严谨性：八字/黄历基于 `lunar-python` 历法库；六爻/梅花/塔罗/卢恩/灵数/解梦/起名为自研确定性算法；**紫微斗数、奇门遁甲、大六壬、风水**等需专业排盘/实地勘测，本项目未做自动排盘，AI 会如实说明、绝不编造。
- **测算工具按需发放**：界面上测算工具不会一开始就显示，而是由 AI 先生了解需求后，判断需要哪项术数，再发放对应工具（回复末尾带 `【工具：key】` 标记，前端解析后显示）。咨询类问题不发放工具。
- 笔画基准说明：**起名/测名的五格数理按康熙笔画**（姓名学惯例）；**测字起卦按简体（现代通用）笔画**（以「数」入卦）。两者用途不同、基准各异，均已注明。库外字会如实提示。
- 传统术数仅供文化参考与心理疏导，不替代医疗、法律与投资决策。
