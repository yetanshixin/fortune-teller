/* ============================================================
   玄机先生 · AI 算命先生 — 前端逻辑
   - 对话咨询 + 术数测算（八字/六爻/梅花/塔罗/卢恩/灵数/择日/解梦/起名）
   - 排盘结果由后端确定性算法计算，注入对话后由大模型解读
   - 设置：切换模型、自定义 API Key（无效自动回退默认 Key）
   - 数据存 localStorage，axios 对接 FastAPI，支持 SSE 流式输出
   ============================================================ */
(() => {
  'use strict';

  /* ---------------- 配置 ---------------- */
  const API_BASE = location.protocol === 'file:' ? 'http://localhost:8000' : '';
  const STORAGE_KEY = 'fortune-teller:conversations';
  const SETTINGS_KEY = 'fortune-teller:settings';
  const THEME_KEY = 'fortune-teller:theme';

  const MODELS = [
    { key: 'deepseek-flash', name: '⚡ deepseek-flash', desc: '极速响应 · 日常测算首选' },
    { key: 'deepseek-v4-pro', name: '🧠 deepseek-v4-pro', desc: '更强能力 · 更高质量解读' },
  ];

  /* ---------------- 术数方法定义 ---------------- */
  const METHODS = [
    { key: 'bazi', name: '八字', emoji: '📜', desc: '四柱八字 · 五行十神 · 大运' },
    { key: 'liuyao', name: '六爻', emoji: '🪙', desc: '摇卦纳甲 · 本卦变卦 · 六亲世应' },
    { key: 'meihua', name: '梅花易数', emoji: '🌸', desc: '数字/时间/测字起卦' },
    { key: 'tarot', name: '塔罗', emoji: '🎴', desc: '78 张韦特塔罗 · 多牌阵' },
    { key: 'runes', name: '卢恩符文', emoji: 'ᚱ', desc: '北欧 24 符文 · 抽符占卜' },
    { key: 'numerology', name: '生命灵数', emoji: '🔢', desc: '毕达哥拉斯灵数 · 主数' },
    { key: 'huangli', name: '黄历择日', emoji: '📅', desc: '宜忌 · 建除 · 冲煞 · 吉神方位' },
    { key: 'dream', name: '解梦', emoji: '💭', desc: '周公解梦 · 梦境关键词' },
    { key: 'naming', name: '起名', emoji: '📛', desc: '五行补益 · 五格数理 · 字义' },
    { key: 'name_fortune', name: '测名', emoji: '📝', desc: '姓名五格数理 · 五行 · 吉凶' },
    { key: 'cezi', name: '测字', emoji: '🖋', desc: '一字测事 · 拆字断卦' },
    { key: 'company_naming', name: '公司取名', emoji: '🏢', desc: '商号 · 行业 · 吉祥字' },
  ];

  const WELCOME_SUGGESTIONS = [
    '帮我看看八字运势',
    '问一下今年的感情',
    '测测这件事的吉凶',
    '给女儿起个名字',
    '我做了个梦，帮我解解',
    '最近财运如何',
  ];

  const ICON = {
    send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22 11 13 2 9 22 2Z"/></svg>',
    stop: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2.5"/></svg>',
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>',
    moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  };

  /* ---------------- DOM ---------------- */
  const $ = (s) => document.querySelector(s);
  const els = {
    messages: $('#messages'),
    input: $('#input'),
    send: $('#send'),
    newChat: $('#new-chat'),
    settingsToggle: $('#settings-toggle'),
    chatList: $('#chat-list'),
    themeToggle: $('#theme-toggle'),
    sidebar: $('#sidebar'),
    sidebarBackdrop: $('#sidebar-backdrop'),
    sidebarToggle: $('#sidebar-toggle'),
    status: $('#chat-status'),
    statusText: $('#status-text'),
    modelName: $('#model-name'),
    // 术数面板
    divinationModal: $('#divination-modal'),
    divinationClose: $('#divination-close'),
    divinationTitle: $('#divination-title'),
    divinationForm: $('#divination-form'),
    // 设置
    settings: $('#settings'),
    settingsClose: $('#settings-close'),
    modelOptions: $('#model-options'),
    settingsApiKey: $('#settings-api-key'),
    settingsSave: $('#settings-save'),
  };

  /* ---------------- 状态 ---------------- */
  let conversations = load();
  let currentId = null;
  let messages = [];
  let streaming = false;
  let abortCtrl = null;
  let settings = loadSettings();
  let activeMethod = 'bazi';
  let activeToolKey = null;   // 当前打开的术数按钮 key，算完后销毁

  /* ---------------- 工具函数 ---------------- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  function renderMarkdown(text) {
    if (window.marked && window.DOMPurify) {
      try {
        const html = window.marked.parse(text, { gfm: true, breaks: true });
        return window.DOMPurify.sanitize(html);
      } catch (e) { /* 回退纯文本 */ }
    }
    return escapeHtml(text).replace(/\n/g, '<br>');
  }

  // 从 AI 回复中提取「工具发放」标记（【工具：bazi,liuyao】），返回工具 key 列表与干净文本
  function extractTools(text) {
    const tools = [];
    const re = /【工具[:：]([^】]+)】/g;
    let m;
    while ((m = re.exec(text)) !== null) {
      m[1].split(/[,，]/).forEach((t) => {
        const key = t.trim();
        if (METHODS.some((x) => x.key === key) && !tools.includes(key)) tools.push(key);
      });
    }
    const clean = text.replace(re, '').replace(/\n{3,}/g, '\n\n').trim();
    return { tools, clean };
  }

  function enhanceCodeBlocks(container) {
    container.querySelectorAll('pre').forEach((pre) => {
      if (pre.querySelector('.code-copy')) return;
      const btn = document.createElement('button');
      btn.className = 'code-copy';
      btn.type = 'button';
      btn.textContent = '复制';
      btn.addEventListener('click', async () => {
        const code = pre.querySelector('code')?.innerText ?? pre.innerText;
        try { await navigator.clipboard.writeText(code); btn.textContent = '已复制'; }
        catch {
          const ta = document.createElement('textarea');
          ta.value = code; document.body.appendChild(ta); ta.select();
          document.execCommand('copy'); document.body.removeChild(ta); btn.textContent = '已复制';
        }
        setTimeout(() => (btn.textContent = '复制'), 1500);
      });
      pre.appendChild(btn);
    });
  }

  function copyText(text) {
    const done = () => showToast('已复制');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, () => { fallbackCopy(text); done(); });
    } else {
      fallbackCopy(text);
      done();
    }
  }

  function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch { /* 忽略 */ }
    document.body.removeChild(ta);
  }

  function showToast(msg) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('is-show');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('is-show'), 1500);
  }

  function scrollToBottom() {
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function inner() {
    let el = els.messages.querySelector('.messages__inner');
    if (!el) {
      el = document.createElement('div');
      el.className = 'messages__inner';
      els.messages.appendChild(el);
    }
    return el;
  }

  /* ---------------- 本地存储 ---------------- */
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const data = raw ? JSON.parse(raw) : [];
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }

  function persist() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations)); } catch { /* 忽略 */ }
  }

  function save() {
    const convo = conversations.find((c) => c.id === currentId);
    if (convo) { convo.messages = messages; convo.updatedAt = Date.now(); }
    conversations.sort((a, b) => b.updatedAt - a.updatedAt);
    persist();
  }

  function loadSettings() {
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      const d = raw ? JSON.parse(raw) : {};
      return {
        model: d.model === 'deepseek-v4-pro' ? 'deepseek-v4-pro' : 'deepseek-flash',
        apiKey: typeof d.apiKey === 'string' ? d.apiKey : '',
      };
    } catch { return { model: 'deepseek-flash', apiKey: '' }; }
  }

  function persistSettings() {
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch { /* 忽略 */ }
  }

  /* ---------------- 会话管理 ---------------- */
  function createConversation() {
    const id = 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    const convo = { id, title: '新对话', messages: [], updatedAt: Date.now() };
    conversations.unshift(convo);
    currentId = id;
    messages = convo.messages;
    persist();
    renderChatList();
    renderMessages();
    focusInput();
  }

  function switchChat(id) {
    if (streaming) stopGeneration();
    const convo = conversations.find((c) => c.id === id);
    if (!convo) return;
    currentId = id;
    messages = convo.messages;
    renderChatList();
    renderMessages();
    closeSidebar();
  }

  function deleteChat(id) {
    if (streaming) stopGeneration();
    conversations = conversations.filter((c) => c.id !== id);
    persist();  // 先持久化删除结果，避免刷新后复活
    if (currentId === id) {
      if (conversations.length > 0) switchChat(conversations[0].id);
      else { currentId = null; messages = []; renderChatList(); renderMessages(); }
    } else { renderChatList(); }
  }

  function renderChatList() {
    els.chatList.innerHTML = '';
    if (conversations.length === 0) {
      els.chatList.innerHTML = '<li class="chat-list__empty">暂无历史对话</li>';
      return;
    }
    for (const c of conversations) {
      const li = document.createElement('li');
      li.className = 'chat-item' + (c.id === currentId ? ' is-active' : '');
      li.dataset.id = c.id;
      li.innerHTML =
        '<button class="chat-item__main"><span class="chat-item__title">' + escapeHtml(c.title) + '</span></button>' +
        '<button class="chat-item__del" title="删除对话">' + ICON.trash + '</button>';
      els.chatList.appendChild(li);
    }
  }

  /* ---------------- 消息渲染 ---------------- */
  function createBubble(role, content) {
    const row = document.createElement('div');
    row.className = 'message message--' + (role === 'user' ? 'user' : 'assistant');
    if (role === 'assistant') {
      row.innerHTML = '<div class="avatar avatar--bot">玄</div><div class="bubble bubble--bot"></div>';
    } else {
      row.innerHTML = '<div class="bubble bubble--user"></div>';
    }
    const bubble = row.querySelector('.bubble');
    if (role === 'assistant') {
      bubble.innerHTML = renderMarkdown(content);
      enhanceCodeBlocks(bubble);
    } else {
      bubble.textContent = content;
    }
    return { row, bubble };
  }

  function renderMessages() {
    els.messages.innerHTML = '';
    const box = inner();
    if (messages.length === 0) { box.appendChild(buildWelcome()); return; }
    for (const m of messages) {
      if (m.role === 'divination') box.appendChild(buildDivinationCard(m.kind, m.data));
      else if (m.role === 'tool') box.appendChild(buildToolCard(m.tools));
      else box.appendChild(createBubble(m.role, m.content).row);
    }
    scrollToBottom();
  }

  function buildWelcome() {
    const el = document.createElement('div');
    el.className = 'welcome';
    el.innerHTML =
      '<div class="welcome__icon">🔮</div>' +
      '<h1 class="welcome__title">有缘人，你来了</h1>' +
      '<p class="welcome__subtitle">我是玄机先生，精通八字、六爻、梅花、塔罗、卢恩、灵数、黄历择日、起名、解梦等术数</p>' +
      '<p class="welcome__desc">想算什么，尽管开口——问感情、问财运、测吉凶、看运势、起名、择日、解梦、做决策皆可。' +
      '我会先问清来龙去脉，再依据排盘与卦象，把道理一条条讲给你听。</p>' +
      '<div class="suggestions">' +
      WELCOME_SUGGESTIONS.map((s) => '<button class="suggestion" data-prompt="' + escapeHtml(s) + '">' + escapeHtml(s) + '</button>').join('') +
      '</div>';
    return el;
  }

  /* ---------------- 排盘卡片 ---------------- */
  function buildDivinationCard(kind, data) {
    const { html } = formatDivination(kind, data);
    const row = document.createElement('div');
    row.className = 'message message--assistant';
    row.innerHTML = '<div class="avatar avatar--bot">卦</div><div class="bubble bubble--bot div-card-host"></div>';
    row.querySelector('.div-card-host').innerHTML = html;
    return row;
  }

  function yaoLineHTML(yang, moving) {
    const seg = '<span style="flex:1;background:var(--gold-soft);border-radius:3px;height:6px;display:block"></span>';
    const cls = moving ? ' style="box-shadow:0 0 8px rgba(212,175,55,0.8)"' : '';
    if (yang) return '<div style="display:flex;width:88px;height:6px"' + cls + '>' + seg + '</div>';
    return '<div style="display:flex;width:88px;height:6px;gap:16px"' + cls + '>' + seg + seg + '</div>';
  }

  function hexagramHTML(info, movingPositions) {
    const lines = [];
    for (let i = 5; i >= 0; i--) {
      const bit = (info.binary >> i) & 1;
      const moving = movingPositions && movingPositions.includes(i + 1);
      lines.push(
        '<div class="yao" style="display:flex;align-items:center;gap:10px;justify-content:center">' +
        yaoLineHTML(bit === 1, moving) +
        '</div>'
      );
    }
    return lines.join('');
  }

  /* ---------------- 排盘结果格式化（text 注入 AI，html 展示） ---------------- */
  function formatDivination(kind, data) {
    switch (kind) {
      case 'bazi': return formatBazi(data);
      case 'liuyao': return formatLiuYao(data);
      case 'meihua': return formatMeiHua(data);
      case 'tarot': return formatTarot(data);
      case 'runes': return formatRunes(data);
      case 'numerology': return formatNumerology(data);
      case 'huangli': return formatHuangLi(data);
      case 'dream': return formatDream(data);
      case 'naming': return formatNaming(data);
      case 'name_fortune': return formatNameFortune(data);
      case 'company_naming': return formatCompanyNaming(data);
      default: return { text: '', html: '' };
    }
  }

  function formatBazi(d) {
    const pillars = d.pillars;
    const text = [
      '【测算数据 · 八字排盘】',
      `出生：${d.solar}（公历），${d.lunar}，${d.gender}`,
      `生肖：${d.shengxiao}；日主：${d.day_master}`,
      '四柱：' + pillars.map((p) => `${p.name} ${p.ganzhi}（${p.wuxing}，纳音${p.nayin}，藏干${p.hide_gan.join('')}）`).join('；'),
      `五行统计：${JSON.stringify(d.wuxing_count)}；缺失：${d.missing_wuxing.join('、') || '无'}`,
      `命宫 ${d.ming_gong.ganzhi}，身宫 ${d.shen_gong}，胎元 ${d.tai_yuan.ganzhi}`,
      `起运：${d.qi_yun.start_year}年${d.qi_yun.start_month}月${d.qi_yun.start_day}天（${d.qi_yun.forward ? '顺排' : '逆排'}）`,
      '大运：' + d.da_yun.slice(0, 8).map((y) => `${y.age}岁 ${y.ganzhi}`).join('，'),
      '',
      '请先生据此为我解读八字命理，结合我的问题详细分析。',
    ].join('\n');

    const rows = pillars.map((p) =>
      `<tr><th>${p.name}</th><td>${p.ganzhi}</td><td>${p.gan} · ${p.zhi}</td><td>${p.wuxing}</td><td>${p.nayin}</td><td>${p.hide_gan.join('')}</td><td>${p.shishen_gan}/${(p.shishen_zhi || []).join('')}</td></tr>`
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">📜 八字排盘</div><div class="div-card__body">' +
      `<table class="pillar-table"><tr><th>柱</th><th>干支</th><th>天干·地支</th><th>五行</th><th>纳音</th><th>藏干</th><th>十神</th></tr>${rows}</table>` +
      `<p>日主 <b>${d.day_master}</b> · 生肖 ${d.shengxiao} · ${d.gender}</p>` +
      `<p>五行：${Object.entries(d.wuxing_count).map(([k, v]) => `${k}${v}`).join(' ')}` +
      (d.missing_wuxing.length ? `　<span style="color:var(--cinnabar)">缺 ${d.missing_wuxing.join('、')}</span>` : '') + `</p>` +
      `<p>命宫 ${d.ming_gong.ganzhi} · 身宫 ${d.shen_gong} · 胎元 ${d.tai_yuan.ganzhi}</p>` +
      `<p>起运 ${d.qi_yun.start_year}年${d.qi_yun.start_month}月 · 大运 ${d.da_yun.slice(0, 8).map((y) => y.ganzhi).join(' → ')}</p>` +
      '</div></div>';
    return { text, html };
  }

  function formatLiuYao(d) {
    const yaoRows = d.yao.map((y) =>
      `${y.pos_name}爻（${y.label}，纳甲${y.najia_zhi}，${y.liuqin}${y.shi_ying ? '·' + y.shi_ying : ''}）`
    ).join('；');
    const text = [
      '【测算数据 · 六爻排盘】',
      `本卦：${d.ben.full_name}（${d.ben.guaci}）`,
      d.changed ? `变卦：${d.bian.full_name}（${d.bian.guaci}）` : '本卦无动爻，未生变卦。',
      `卦宫：${d.gong}（${d.gong_wuxing}），世爻在第${d.shi_yao}爻，应爻在第${d.ying_yao}爻。`,
      `爻象：${yaoRows}`,
      `卦象：${d.ben.daxiang}`,
      '',
      '请先生据此解卦，结合我的问题详细分析。',
    ].join('\n');

    const yaoList = d.yao.slice().reverse().map((y) =>
      `<div style="display:flex;align-items:center;gap:8px;justify-content:center;font-size:11px;color:var(--text-dim)">` +
      `${yaoLineHTML(y.yin_yang === '阳', y.moving)}` +
      `<span style="min-width:80px">${y.najia_zhi} ${y.liuqin}${y.shi_ying ? ' ' + y.shi_ying : ''}${y.moving ? ' ○' : ''}</span>` +
      `</div>`
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">🪙 六爻排盘</div><div class="div-card__body">' +
      '<div class="hexagram-wrap">' +
      `<div class="hexagram-block"><div class="hex-name">本卦 · ${d.ben.full_name}</div>${yaoList}</div>` +
      (d.changed ? `<div class="hexagram-block"><div class="hex-name">变卦 · ${d.bian.full_name}</div>${hexagramHTML(d.bian)}</div>` : '') +
      '</div>' +
      `<p><b>${d.ben.guaci}</b>　${d.ben.daxiang}</p>` +
      `<p>卦宫 ${d.gong}（${d.gong_wuxing}） · 世${d.shi_yao}爻 应${d.ying_yao}爻</p>` +
      '</div></div>';
    return { text, html };
  }

  function formatMeiHua(d) {
    const isWord = !!(d.extra && d.extra.word);
    const wordLines = isWord ? [
      `测字：「${d.extra.word}」，${d.extra.chars.map((c) => `${c.char}${c.strokes}画${c.wuxing ? '（五行' + c.wuxing + '）' : ''}`).join('、')}`,
      '（拆字解义由先生结合卦象与字义展开）',
    ] : [];
    const text = [
      isWord ? '【测算数据 · 测字】' : '【测算数据 · 梅花易数】',
      d.method,
      ...wordLines,
      `本卦：${d.ben.full_name}（${d.ben.guaci}）`,
      `互卦：${d.hu.full_name}（${d.hu.guaci}）`,
      `变卦：${d.bian.full_name}（${d.bian.guaci}）`,
      `动爻：第${d.dong_yao}爻（${d.ti}为体，${d.yong}为用）`,
      `卦象：${d.ben.daxiang}`,
      '',
      '请先生据此解卦，结合我的问题详细分析。',
    ].join('\n');

    const block = (info, movingPositions) =>
      `<div class="hexagram-block"><div class="hex-name">${info.full_name}</div>${hexagramHTML(info, movingPositions)}</div>`;
    const wordHead = isWord
      ? `<p style="color:var(--gold-soft)">${escapeHtml(d.extra.word)}　${d.extra.chars.map((c) => `${c.char}${c.strokes}画` + (c.wuxing ? '·' + c.wuxing : '')).join('　')}</p>`
      : '';
    const html =
      '<div class="div-card"><div class="div-card__head">' + (isWord ? '🖋 测字' : '🌸 梅花易数') + '</div><div class="div-card__body">' +
      `<p style="color:var(--text-dim)">${d.method}</p>` +
      wordHead +
      '<div class="hexagram-wrap">' +
      block(d.ben, [d.dong_yao]) + block(d.hu, null) + block(d.bian, null) +
      '</div>' +
      `<p><b>${d.ben.guaci}</b>　${d.ben.daxiang}</p>` +
      `<p>动爻第${d.dong_yao}爻 · ${d.ti}为体，${d.yong}为用</p>` +
      '</div></div>';
    return { text, html };
  }

  function formatTarot(d) {
    const text = [
      '【测算数据 · 塔罗牌】',
      `牌阵：${d.spread}`,
      ...d.cards.map((c) => `${c.position}：${c.name}（${c.reversed ? '逆位' : '正位'}）——${c.meaning}`),
      '',
      '请先生据此解牌，结合我的问题详细分析。',
    ].join('\n');

    const cards = d.cards.map((c) =>
      `<div class="tarot-card${c.reversed ? ' is-reversed' : ''}">` +
      `<div class="tarot-card__pos">${c.position}</div>` +
      `<div class="tarot-card__name">${escapeHtml(c.name)}</div>` +
      (c.reversed ? '<div class="tarot-card__rev">逆位</div>' : '') +
      `<div class="tarot-card__meaning">${escapeHtml(c.meaning)}</div>` +
      '</div>'
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">🎴 塔罗牌</div><div class="div-card__body">' +
      `<div class="tarot-grid">${cards}</div></div></div>`;
    return { text, html };
  }

  function formatRunes(d) {
    const text = [
      '【测算数据 · 卢恩符文】',
      ...d.runes.map((r) => `符文 ${r.glyph} ${r.name}（${r.reversed ? '逆位' : '正位'}）——${r.meaning}`),
      '',
      '请先生据此解读符文，结合我的问题详细分析。',
    ].join('\n');

    const runes = d.runes.map((r) =>
      `<div class="rune"><div class="rune__glyph">${r.glyph}</div><div class="rune__name">${r.name}${r.reversed ? '（逆）' : ''}</div>` +
      `<div style="font-size:11px;color:var(--text-dim)">${escapeHtml(r.meaning)}</div></div>`
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">ᚱ 卢恩符文</div><div class="div-card__body">' +
      `<div class="rune-list">${runes}</div></div></div>`;
    return { text, html };
  }

  function formatNumerology(d) {
    const text = [
      '【测算数据 · 生命灵数】',
      `生日：${d.birthday}`,
      `生命灵数：${d.life_path} —— ${d.life_path_meaning}`,
      (d.name_number ? `姓名灵数：${d.name_number} —— ${d.name_number_meaning}` : ''),
      '',
      '请先生据此解读，结合我的情况详细分析。',
    ].filter(Boolean).join('\n');

    const html =
      '<div class="div-card"><div class="div-card__head">🔢 生命灵数</div><div class="div-card__body">' +
      `<p>生命灵数 <span style="font-family:var(--serif);font-size:26px;color:var(--gold-soft)">${d.life_path}</span></p>` +
      `<p>${escapeHtml(d.life_path_meaning)}</p>` +
      (d.name_number ? `<p>姓名灵数 <b>${d.name_number}</b>：${escapeHtml(d.name_number_meaning || '')}</p>` : '') +
      '</div></div>';
    return { text, html };
  }

  function formatHuangLi(d) {
    const text = [
      '【测算数据 · 黄历择日】',
      `${d.solar}（公历），${d.lunar}`,
      `干支：${d.year_ganzhi}年 ${d.month_ganzhi}月 ${d.day_ganzhi}日`,
      `建除：${d.zhi_xing}；九星：${d.jiu_xing}`,
      `冲：${d.chong}，煞：${d.sha}`,
      `彭祖百忌：${d.peng_zu.gan}；${d.peng_zu.zhi}`,
      `宜：${d.yi.join('、') || '无'}`,
      `忌：${d.ji.join('、') || '无'}`,
      `吉神方位：财神${d.position.cai}，喜神${d.position.xi}，福神${d.position.fu}`,
      d.matter ? `所问事项：${d.matter}` : '',
      '',
      '请先生据此判断该日吉凶是否适合我所问之事，详细说明。',
    ].join('\n');

    const html =
      '<div class="div-card"><div class="div-card__head">📅 黄历择日</div><div class="div-card__body">' +
      `<p><b>${d.lunar}</b> · ${d.day_ganzhi}日</p>` +
      `<p>建除 <b>${d.zhi_xing}</b> · ${d.jiu_xing} · 冲${d.chong} 煞${d.sha}</p>` +
      `<p style="color:var(--cinnabar)">忌：${d.ji.join('、') || '无'}</p>` +
      `<p style="color:var(--gold-soft)">宜：${d.yi.join('、') || '无'}</p>` +
      `<p>财神 ${d.position.cai} · 喜神 ${d.position.xi} · 福神 ${d.position.fu}</p>` +
      '</div></div>';
    return { text, html };
  }

  function formatDream(d) {
    if (!d.matched) {
      const text = '【测算数据 · 解梦】\n梦境描述：' + d.text + '\n词典未直接命中关键词，请先生结合梦境整体氛围与上下文，用传统解梦思路为我解读。\n';
      const html = '<div class="div-card"><div class="div-card__head">💭 解梦</div><div class="div-card__body">' +
        '<p>已记录你的梦境，请先生为你解读。</p></div></div>';
      return { text, html };
    }
    const text = [
      '【测算数据 · 解梦】',
      '梦境描述：' + d.text,
      '命中关键词：',
      ...d.hits.map((h) => `· ${h.keyword}：${h.meaning}`),
      '',
      '请先生据此结合上下文为我解梦，详细分析。',
    ].join('\n');

    const hits = d.hits.map((h) =>
      `<p style="margin:6px 0"><b style="color:var(--gold-soft)">${escapeHtml(h.keyword)}</b>：${escapeHtml(h.meaning)}</p>`
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">💭 解梦</div><div class="div-card__body">' + hits + '</div></div>';
    return { text, html };
  }

  function formatNaming(d) {
    if (d.type === 'foreign') {
      const text = [
        '【测算数据 · 起名】',
        `姓氏：${d.surname}，${d.gender}`,
        '候选名字：',
        ...d.candidates.map((c) => `${c.name}（${c.meaning}）`),
        '',
        '请先生据此为我推荐最合适的名字，结合音韵、字义、文化内涵详细说明理由。',
      ].join('\n');
      const names = d.candidates.map((c) =>
        `<div class="name-candidate"><div class="name-candidate__name">${escapeHtml(c.name)}</div>` +
        `<div class="name-candidate__meaning">${escapeHtml(c.meaning)}</div></div>`
      ).join('');
      const html =
        '<div class="div-card"><div class="div-card__head">📛 起名 · ' + escapeHtml(d.surname) + '·' + (d.gender === '男' ? '男孩' : '女孩') + '</div><div class="div-card__body">' +
        `<div class="name-grid">${names}</div></div></div>`;
      return { text, html };
    }
    const text = [
      '【测算数据 · 起名】',
      `姓氏：${d.surname}（康熙${d.surname_strokes}画），${d.gender}`,
      `建议补益五行：${d.suggest_wuxing.join('、')}`,
      '候选名字：',
      ...d.candidates.slice(0, 10).map((c) =>
        `${c.full_name}（${c.chars.map((ch) => ch.char + ch.wuxing).join('')}；五格 天${c.wuge.天格} 人${c.wuge.人格} 地${c.wuge.地格} 外${c.wuge.外格} 总${c.wuge.总格}；${c.meaning}）`
      ),
      '',
      '请先生据此为我推荐最合适的名字，并结合五行、五格数理、字义、音韵详细说明理由。',
    ].join('\n');

    const names = d.candidates.slice(0, 12).map((c) =>
      `<div class="name-candidate"><div class="name-candidate__name">${c.full_name}</div>` +
      `<div class="name-candidate__meaning">${escapeHtml(c.meaning)}</div>` +
      `<div class="name-candidate__wuge">${c.chars.map((ch) => ch.char + ch.wuxing).join(' ')} · 天${c.wuge.天格}人${c.wuge.人格}地${c.wuge.地格}外${c.wuge.外格}总${c.wuge.总格}</div>` +
      '</div>'
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">📛 起名 · ' + escapeHtml(d.surname) + '姓' + (d.gender === '男' ? '男孩' : '女孩') + '</div><div class="div-card__body">' +
      `<p>建议补益五行：<b style="color:var(--gold-soft)">${d.suggest_wuxing.join('、')}</b></p>` +
      `<div class="name-grid">${names}</div></div></div>`;
    return { text, html };
  }

  function formatNameFortune(d) {
    if (d.type === 'english') {
      const text = [
        '【测算数据 · 测名】',
        `姓名：${d.name}（英文名）`,
        `毕达哥拉斯灵数：${d.number} —— ${d.meaning}`,
        '',
        '请先生据此分析这个名字的运势与性格，结合灵数含义详细说明。',
      ].join('\n');
      const html =
        '<div class="div-card"><div class="div-card__head">📝 测名 · ' + escapeHtml(d.name) + '</div><div class="div-card__body">' +
        `<p>毕达哥拉斯灵数 <span style="font-family:var(--serif);font-size:26px;color:var(--gold-soft)">${d.number}</span></p>` +
        `<p>${escapeHtml(d.meaning)}</p></div></div>`;
      return { text, html };
    }
    const charDesc = d.chars.map((c) => c.strokes ? `${c.char}（${c.strokes}画·${c.wuxing}）` : `${c.char}（笔画未知）`).join(' ');
    const text = [
      '【测算数据 · 测名】',
      `姓名：${d.name}（姓${d.surname} ${d.surname_strokes}画，名${d.given}）`,
      `用字：${charDesc}`,
      d.unknown_chars.length ? `注意：${d.unknown_chars.join('、')} 的笔画暂不在字库，五格数理无法精确计算。` : '',
      d.wuge ? `五格数理：天格${d.wuge.天格} 人格${d.wuge.人格} 地格${d.wuge.地格} 外格${d.wuge.外格} 总格${d.wuge.总格}` : '',
      d.wuxing_missing ? `姓名用字五行缺失：${d.wuxing_missing.join('、')}` : '',
      '',
      '请先生据此分析这个名字的运势吉凶，结合五格数理、五行、字义与音韵详细说明。',
    ].filter(Boolean).join('\n');

    const charsHtml = d.chars.map((c) =>
      `<span style="margin-right:10px">${escapeHtml(c.char)}${c.strokes ? `（${c.strokes}画·${c.wuxing}）` : '（笔画未知）'}</span>`
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">📝 测名 · ' + escapeHtml(d.name) + '</div><div class="div-card__body">' +
      (d.wuge ? `<p>五格数理：天${d.wuge.天格} · 人${d.wuge.人格} · 地${d.wuge.地格} · 外${d.wuge.外格} · 总${d.wuge.总格}</p>` : '') +
      `<p>用字：${charsHtml}</p>` +
      (d.unknown_chars.length ? `<p style="color:var(--cinnabar)">${d.unknown_chars.join('、')} 的笔画不在字库，五格暂无法精确计算</p>` : '') +
      (d.wuxing_missing ? `<p>五行缺失：${d.wuxing_missing.join('、')}</p>` : '') +
      '</div></div>';
    return { text, html };
  }

  function formatCompanyNaming(d) {
    const text = [
      '【测算数据 · 公司取名】',
      `行业：${d.industry}` + (d.preference ? `；期望寓意：${d.preference}` : ''),
      '候选商号：',
      ...d.candidates.map((c) => `${c.name}（${c.meaning}）`),
      '',
      '请先生据此为公司推荐最合适的商号，结合行业、寓意、音韵、易记程度详细说明理由。',
    ].join('\n');

    const names = d.candidates.map((c) =>
      `<div class="name-candidate"><div class="name-candidate__name">${escapeHtml(c.name)}</div>` +
      `<div class="name-candidate__meaning">${escapeHtml(c.meaning)}</div>` +
      `<div class="name-candidate__wuge">${c.chars.map((ch) => ch.char + ch.wuxing).join(' ')}</div>` +
      '</div>'
    ).join('');
    const html =
      '<div class="div-card"><div class="div-card__head">🏢 公司取名 · ' + escapeHtml(d.industry) + '</div><div class="div-card__body">' +
      `<div class="name-grid">${names}</div></div></div>`;
    return { text, html };
  }

  /* ---------------- 术数面板 ---------------- */
  function renderForm(method) {
    els.divinationForm.innerHTML = '';
    const form = document.createElement('div');
    switch (method) {
      case 'bazi': form.appendChild(formBazi()); break;
      case 'liuyao': form.appendChild(formLiuYao()); break;
      case 'meihua': form.appendChild(formMeiHua()); break;
      case 'tarot': form.appendChild(formTarot()); break;
      case 'runes': form.appendChild(formRunes()); break;
      case 'numerology': form.appendChild(formNumerology()); break;
      case 'huangli': form.appendChild(formHuangLi()); break;
      case 'dream': form.appendChild(formDream()); break;
      case 'naming': form.appendChild(formNaming()); break;
      case 'name_fortune': form.appendChild(formNameFortune()); break;
      case 'cezi': form.appendChild(formCezi()); break;
      case 'company_naming': form.appendChild(formCompanyNaming()); break;
    }
    els.divinationForm.appendChild(form);
  }

  function field(label, inner) {
    const div = document.createElement('div');
    div.className = 'field';
    const labelEl = document.createElement('label');
    labelEl.textContent = label;
    div.appendChild(labelEl);
    if (typeof inner === 'string') {
      div.insertAdjacentHTML('beforeend', inner);
    } else {
      div.appendChild(inner);   // 支持直接传入 DOM 元素
    }
    return div;
  }

  // 分段选择控件（男/女、公历/农历等），内置点击高亮
  function segControl(options, activeValue) {
    const el = document.createElement('div');
    el.className = 'seg';
    el.innerHTML = options.map((o) =>
      '<button class="' + (o.value === activeValue ? 'is-active' : '') + '" data-v="' + o.value + '">' + o.label + '</button>'
    ).join('');
    el.addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (!b) return;
      el.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x === b));
    });
    return el;
  }

  function formBazi() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">四柱八字排盘</div>' +
      '<div class="div-form__desc">请输入出生信息（公历或农历均可）。时辰用于确定时柱，请尽量准确。</div>';
    const cal = segControl([{ value: 'solar', label: '公历' }, { value: 'lunar', label: '农历' }], 'solar');
    f.appendChild(field('历法', cal));

    const dateRow = document.createElement('div');
    dateRow.className = 'form-row';
    dateRow.appendChild(field('出生日期', '<input type="date" id="bz-date" value="2000-01-01">'));
    dateRow.appendChild(field('时辰', '<input type="time" id="bz-time" value="08:30">'));

    const gender = segControl([{ value: '男', label: '男' }, { value: '女', label: '女' }], '男');

    f.appendChild(dateRow);
    f.appendChild(field('性别', gender));
    f.insertAdjacentHTML('beforeend', '<button class="btn btn--primary" id="bz-submit">排盘测算</button>');

    f.querySelector('#bz-submit').addEventListener('click', () => {
      const [y, m, d] = f.querySelector('#bz-date').value.split('-').map(Number);
      const [hh, mm] = f.querySelector('#bz-time').value.split(':').map(Number);
      const calendar = cal.querySelector('.is-active').dataset.v;
      const genderVal = gender.querySelector('.is-active').dataset.v;
      submitDivination('bazi', { year: y, month: m, day: d, hour: hh, minute: mm, calendar, gender: genderVal });
    });
    return f;
  }

  function formLiuYao() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">六爻纳甲</div>' +
      '<div class="div-form__desc">心中默念所问之事，点击下方按钮虔诚摇卦。卦象一次起定、心诚则灵，请先想好所问之事再摇。系统以三枚铜钱起卦：花记 3、字记 2，三枚相加，6=老阴（动）、7=少阳、8=少阴、9=老阳（动）。</div>';

    const box = document.createElement('div');
    box.style.marginTop = '12px';
    f.appendChild(box);

    function renderVirtual() {
      box.innerHTML = '';
      let lines = null;
      const shakeBtn = document.createElement('button');
      shakeBtn.className = 'btn btn--primary';
      shakeBtn.textContent = '🎲 虔诚摇卦';
      const result = document.createElement('div');

      box.appendChild(shakeBtn);
      box.appendChild(result);

      shakeBtn.addEventListener('click', () => {
        if (shakeBtn.disabled) return;
        shakeBtn.textContent = '摇卦中…';
        shakeBtn.disabled = true;
        lines = Array.from({ length: 6 }, () => [6, 7, 8, 9][Math.floor(Math.random() * 4)]);
        setTimeout(() => {
          shakeBtn.textContent = '🎲 卦已起定，呈与先生…';
          // 摇卦即提交，结果在对话流卡片里展示，无中间态
          submitDivination('liuyao', { lines });
        }, 900);
      });
    }

    renderVirtual();
    return f;
  }

  function formMeiHua() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">梅花易数</div>' +
      '<div class="div-form__desc">可用数字、时间或汉字起卦。数字起卦请填 1~3 个正整数。</div>';
    const type = document.createElement('div');
    type.className = 'seg';
    type.innerHTML = '<button class="is-active" data-v="number">数字起卦</button><button data-v="time">时间起卦</button><button data-v="word">测字起卦</button>';
    f.appendChild(type);

    const box = document.createElement('div');
    box.style.marginTop = '12px';
    f.appendChild(box);

    function render(v) {
      if (v === 'number') {
        box.innerHTML = '';
        box.appendChild(field('数字（用逗号分隔）', '<input id="mh-nums" placeholder="例如：3,5,9">'));
      } else if (v === 'time') {
        box.innerHTML = '';
        box.appendChild(field('时间', '<input type="datetime-local" id="mh-time">'));
      } else {
        box.innerHTML = '';
        box.appendChild(field('汉字（1~2 字）', '<input id="mh-word" placeholder="例如：财运">'));
        box.insertAdjacentHTML('beforeend', '<div class="div-form__desc" style="color:var(--text-faint)">测字仅支持内置常用字笔画库，库外字会提示。</div>');
      }
      const btn = document.createElement('button');
      btn.className = 'btn btn--primary';
      btn.textContent = '起卦';
      btn.id = 'mh-submit';
      box.appendChild(btn);
      btn.addEventListener('click', () => {
        if (v === 'number') {
          const numbers = box.querySelector('#mh-nums').value.split(/[,，\s]+/).filter(Boolean).map(Number);
          submitDivination('meihua', { type: 'number', numbers });
        } else if (v === 'time') {
          const t = box.querySelector('#mh-time').value;
          submitDivination('meihua', { type: 'time', time: t.replace('T', ' ') });
        } else {
          submitDivination('meihua', { type: 'word', word: box.querySelector('#mh-word').value });
        }
      });
    }

    type.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      type.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x === b));
      render(b.dataset.v);
    });
    render('number');
    return f;
  }

  function formTarot() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">塔罗牌</div>' +
      '<div class="div-form__desc">静心默念你的问题，选择牌阵后抽牌。</div>';
    f.appendChild(field('牌阵',
      '<select id="tr-spread">' +
      '<option value="single">单张 · 整体情况</option>' +
      '<option value="three" selected>三牌阵 · 过去/现在/未来</option>' +
      '<option value="celtic">凯尔特十字 · 十张</option>' +
      '</select>'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '🎴 洗牌抽牌';
    f.appendChild(btn);
    btn.addEventListener('click', () => submitDivination('tarot', { spread: f.querySelector('#tr-spread').value }));
    return f;
  }

  function formRunes() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">卢恩符文</div>' +
      '<div class="div-form__desc">北欧古符文占卜，抽取符文探问运势与指引。</div>';
    f.appendChild(field('抽取数量',
      '<select id="rn-count"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option></select>'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = 'ᚱ 抽取符文';
    f.appendChild(btn);
    btn.addEventListener('click', () => submitDivination('runes', { count: Number(f.querySelector('#rn-count').value) }));
    return f;
  }

  function formNumerology() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">生命灵数</div>' +
      '<div class="div-form__desc">毕达哥拉斯灵数，由生日推算生命灵数。</div>';
    f.appendChild(field('出生日期', '<input type="date" id="nm-date" value="1990-05-15">'));
    f.appendChild(field('英文名（可选，用于姓名灵数）', '<input id="nm-name" placeholder="例如：Alice">'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '测算灵数';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const [y, m, d] = f.querySelector('#nm-date').value.split('-').map(Number);
      const name = f.querySelector('#nm-name').value.trim();
      submitDivination('numerology', { year: y, month: m, day: d, name: name || null });
    });
    return f;
  }

  function formHuangLi() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">黄历择日</div>' +
      '<div class="div-form__desc">查询某日宜忌、建除、冲煞与吉神方位，判断是否适合办事。</div>';
    f.appendChild(field('日期', '<input type="date" id="hl-date">'));
    f.appendChild(field('所问事项（可选）', '<input id="hl-matter" placeholder="例如：结婚、开业、搬家">'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '查询黄历';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const [y, m, d] = f.querySelector('#hl-date').value.split('-').map(Number);
      submitDivination('huangli', { year: y, month: m, day: d, matter: f.querySelector('#hl-matter').value.trim() || null });
    });
    return f;
  }

  function formDream() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">解梦</div>' +
      '<div class="div-form__desc">把梦境尽量详细地描述出来，我会结合关键词与整体氛围为你解读。</div>';
    f.appendChild(field('梦境描述', '<textarea id="dr-text" placeholder="我梦见……"></textarea>'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '解梦';
    f.appendChild(btn);
    btn.addEventListener('click', () => submitDivination('dream', { text: f.querySelector('#dr-text').value }));
    return f;
  }

  function formNaming() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">起名</div>' +
      '<div class="div-form__desc">提供姓氏、性别与语言，为你推演候选好名。</div>';
    const lang = segControl([{ value: 'zh', label: '中文' }, { value: 'en', label: '英文' }, { value: 'ja', label: '日文' }], 'zh');
    f.appendChild(field('语言', lang));
    f.appendChild(field('姓氏', '<input id="nm-surname" maxlength="20" placeholder="例如：张 / Smith / 山田">'));
    const gender = segControl([{ value: '男', label: '男' }, { value: '女', label: '女' }], '男');
    f.appendChild(field('性别', gender));
    f.appendChild(field('生辰（可选，中文名用于五行补益）', '<input type="datetime-local" id="nm-bazi">'));
    f.appendChild(field('期望寓意（可选）', '<input id="nm-pref" placeholder="例如：睿智、温婉">'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '推演名字';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const surname = f.querySelector('#nm-surname').value.trim();
      if (!surname) { alert('请填写姓氏'); return; }
      const genderVal = gender.querySelector('.is-active').dataset.v;
      const bzVal = f.querySelector('#nm-bazi').value;
      let bazi = null;
      if (bzVal) {
        const [date, time] = bzVal.split('T');
        const [y, m, d] = date.split('-').map(Number);
        const [hh, mm] = (time || '00:00').split(':').map(Number);
        bazi = { year: y, month: m, day: d, hour: hh, minute: mm, gender: genderVal, calendar: 'solar' };
      }
      submitDivination('naming', { surname, gender: genderVal, lang: lang.querySelector('.is-active').dataset.v, bazi, preference: f.querySelector('#nm-pref').value.trim() || null });
    });
    return f;
  }

  function formNameFortune() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">测名</div>' +
      '<div class="div-form__desc">输入一个完整姓名：中文/日文汉字推演五格数理，英文名推演毕达哥拉斯灵数。字库外的字会如实提示。</div>';
    f.appendChild(field('姓名', '<input id="nf-name" maxlength="40" placeholder="例如：张伟 / John Smith / 山田太郎">'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '测算姓名';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const name = f.querySelector('#nf-name').value.trim();
      if (!name) { alert('请输入姓名'); return; }
      submitDivination('name_fortune', { name });
    });
    return f;
  }

  function formCompanyNaming() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">公司取名</div>' +
      '<div class="div-form__desc">填写公司所属行业与期望寓意，为你推演吉祥商号。</div>';
    f.appendChild(field('行业', '<input id="cn-industry" maxlength="20" placeholder="例如：科技 / 餐饮 / 贸易">'));
    const length = segControl([{ value: '2', label: '二字' }, { value: '3', label: '三字' }, { value: '4', label: '四字' }], '2');
    f.appendChild(field('商号字数', length));
    f.appendChild(field('期望寓意（可选）', '<input id="cn-pref" placeholder="例如：兴旺、诚信、创新">'));
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '推演商号';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const industry = f.querySelector('#cn-industry').value.trim();
      if (!industry) { alert('请填写行业'); return; }
      submitDivination('company_naming', {
        industry,
        preference: f.querySelector('#cn-pref').value.trim() || null,
        length: Number(length.querySelector('.is-active').dataset.v),
      });
    });
    return f;
  }

  function formCezi() {
    const f = document.createElement('div');
    f.innerHTML =
      '<div class="div-form__title">测字</div>' +
      '<div class="div-form__desc">心中默念所问之事，写下一个字（或两个字）。先生按笔画起卦，再拆字解义。</div>';
    f.appendChild(field('汉字（1~2 字）', '<input id="cz-word" maxlength="2" placeholder="例如：一">'));
    f.insertAdjacentHTML('beforeend', '<div class="div-form__desc" style="color:var(--text-faint)">仅支持内置常用字笔画库，库外字会提示。</div>');
    const btn = document.createElement('button');
    btn.className = 'btn btn--primary';
    btn.textContent = '起卦测字';
    f.appendChild(btn);
    btn.addEventListener('click', () => {
      const word = f.querySelector('#cz-word').value.trim();
      if (!word) { alert('请写一个字'); return; }
      submitDivination('meihua', { type: 'word', word });
    });
    return f;
  }

  /* ---------------- 提交测算 ---------------- */
  async function submitDivination(kind, payload) {
    const btn = els.divinationForm.querySelector('.btn--primary');
    if (btn) { btn.disabled = true; btn.textContent = '测算中…'; }
    try {
      const res = await axios.post(API_BASE + '/api/divination/' + kind, payload, { timeout: 30000 });
      const data = res.data;
      closeDivination();
      await injectDivination(kind, data);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || '测算失败';
      alert('测算失败：' + msg);
      if (btn) { btn.disabled = false; btn.textContent = '重试'; }
    }
  }

  async function injectDivination(kind, data) {
    // 记录排盘卡片消息
    messages.push({ role: 'divination', kind, data });
    destroyTool(activeToolKey);   // 术数用完即销毁对应按钮，防止重复算
    if (messages.length === 1) { const c = conversations.find((x) => x.id === currentId); if (c) c.title = METHODS.find((m) => m.key === kind)?.name || '测算'; }
    const convo = conversations.find((c) => c.id === currentId);
    if (convo && convo.title === '新对话') convo.title = METHODS.find((m) => m.key === kind)?.name || '测算';
    renderMessages();
    save();
    renderChatList();

    // 排盘结果已作为 divination 消息存入 messages，messagesToLLM 会自动注入给 AI 解读
    await streamAssistantReply();
  }

  function destroyTool(key) {
    if (!key) return;
    // 从后往前找第一个 tools 包含 key 的 tool 消息并移除（术数用完即销毁）
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === 'tool' && (m.tools || []).includes(key)) {
        messages.splice(i, 1);
        break;
      }
    }
  }

  /* ---------------- 发送与流式回复 ---------------- */
  function messagesToLLM(extraPrompt) {
    const list = [];
    for (const m of messages) {
      if (m.role === 'divination') {
        list.push({
          role: 'user',
          content: formatDivination(m.kind, m.data).text + '\n（请先向客户表明你已看到这份测算结果，再开始逐条解读。）',
        });
      } else if (m.role === 'user' || m.role === 'assistant') {
        list.push({ role: m.role, content: m.content });
      }
    }
    if (extraPrompt) list.push({ role: 'user', content: extraPrompt });
    return list.slice(-30);
  }

  async function sendMessage() {
    const text = els.input.value.trim();
    if (!text || streaming) return;
    els.input.value = '';
    autoResize();
    updateSendState();

    if (!currentId) createConversation();

    const convo = conversations.find((c) => c.id === currentId);
    if (convo && convo.title === '新对话') {
      convo.title = text.length > 20 ? text.slice(0, 20) + '…' : text;
      renderChatList();
    }

    messages.push({ role: 'user', content: text });
    renderMessages();
    save();

    await streamAssistantReply();
  }

  async function streamAssistantReply(extraPrompt) {
    streaming = true;
    toggleComposer();
    const streamConvoId = currentId;
    const streamMessages = messages;

    const { bubble } = createBubble('assistant', '');
    bubble.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    inner().appendChild(bubble.closest('.message'));
    scrollToBottom();

    let buffer = '';
    let rafId = null;
    let failed = false;
    let interrupted = false;
    let interruptedContent = '';
    const render = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        bubble.innerHTML = renderMarkdown(extractTools(buffer).clean);
        scrollToBottom();
      });
    };

    const history = messagesToLLM(extraPrompt);
    abortCtrl = new AbortController();

    try {
      const res = await axios.post(
        API_BASE + '/api/chat',
        { messages: history, stream: true, model: settings.model, api_key: settings.apiKey || null },
        { responseType: 'stream', adapter: 'fetch', signal: abortCtrl.signal }
      );
      await readSSE(res, (delta) => { buffer += delta; render(); });
    } catch (err) {
      if (axios.isCancel(err)) {
        buffer += buffer ? '\n\n*(已停止生成)*' : '*(已停止生成)*';
      } else if (buffer === '') {
        try { buffer = await fallbackNonStream(history); }
        catch (err2) {
          failed = true;
          buffer = '> ⚠️ 请求失败：' + (err2?.message || err2);
        }
      } else {
        interrupted = true;
        interruptedContent = buffer;   // 已生成的部分内容
        buffer += '\n\n> ⚠️ 生成中断：' + (err?.message || err);
      }
    } finally {
      streaming = false;
      abortCtrl = null;
      toggleComposer();
      const { tools, clean } = extractTools(buffer);
      const displayText = clean || (tools.length ? '（先生递上一门术数，请点击使用）' : buffer);
      bubble.innerHTML = renderMarkdown(displayText);
      enhanceCodeBlocks(bubble);
      if (failed) {
        const retryBtn = document.createElement('button');
        retryBtn.className = 'retry-btn';
        retryBtn.textContent = '🔄 重试';
        retryBtn.addEventListener('click', () => {
          bubble.closest('.message').remove();
          streamAssistantReply();
        });
        bubble.appendChild(retryBtn);
      } else if (interrupted) {
        const contBtn = document.createElement('button');
        contBtn.className = 'retry-btn';
        contBtn.textContent = '▶ 继续生成';
        contBtn.addEventListener('click', () => {
          const partial = extractTools(interruptedContent).clean || interruptedContent;
          streamMessages.push({ role: 'assistant', content: partial });
          bubble.closest('.message').remove();
          streamAssistantReply();
        });
        const regenBtn = document.createElement('button');
        regenBtn.className = 'retry-btn';
        regenBtn.style.marginLeft = '8px';
        regenBtn.textContent = '🔄 重新生成';
        regenBtn.addEventListener('click', () => {
          bubble.closest('.message').remove();
          streamAssistantReply();
        });
        bubble.appendChild(contBtn);
        bubble.appendChild(regenBtn);
      }
      if (clean && !failed && !interrupted) streamMessages.push({ role: 'assistant', content: clean });
      if (tools.length) {
        // 销毁所有旧的未使用术数，只保留最新这 1 个
        for (let i = streamMessages.length - 1; i >= 0; i--) {
          if (streamMessages[i].role === 'tool') streamMessages.splice(i, 1);
        }
        streamMessages.push({ role: 'tool', tools: tools.slice(0, 1) });
      }
      const convo = conversations.find((c) => c.id === streamConvoId);
      if (convo) { convo.messages = streamMessages; convo.updatedAt = Date.now(); }
      conversations.sort((a, b) => b.updatedAt - a.updatedAt);
      persist();
      renderChatList();
      if (currentId === streamConvoId) {
        if (tools.length) renderMessages();   // 重新渲染，在先生回复后展示术数卡片
        else scrollToBottom();
      }
    }
  }

  async function readSSE(response, onDelta) {
    const reader = response.data.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, idx).trim();
        buf = buf.slice(idx + 1);
        if (!line.startsWith('data:')) continue;
        const data = line.slice(5).trim();
        if (data === '[DONE]') return;
        try {
          const obj = JSON.parse(data);
          if (obj.error) throw new Error(obj.error);
          if (obj.delta) onDelta(obj.delta);
        } catch (e) {
          if (e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }
  }

  async function fallbackNonStream(history) {
    const res = await axios.post(
      API_BASE + '/api/chat',
      { messages: history, stream: false, model: settings.model, api_key: settings.apiKey || null },
      { signal: abortCtrl ? abortCtrl.signal : undefined }
    );
    return res.data?.reply || '';
  }

  function stopGeneration() {
    if (abortCtrl) abortCtrl.abort();
  }

  /* ---------------- 输入区 ---------------- */
  function autoResize() {
    els.input.style.height = 'auto';
    els.input.style.height = Math.min(els.input.scrollHeight, 180) + 'px';
  }

  function insertNewline() {
    const el = els.input;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    el.value = el.value.slice(0, start) + '\n' + el.value.slice(end);
    const pos = start + 1;
    el.selectionStart = el.selectionEnd = pos;
    autoResize();
    updateSendState();
  }
  function updateSendState() {
    const empty = !els.input.value.trim();
    els.send.classList.toggle('is-disabled', empty && !streaming);
  }
  function toggleComposer() {
    els.send.classList.toggle('is-streaming', streaming);
    els.send.innerHTML = streaming ? ICON.stop : ICON.send;
    els.send.title = streaming ? '停止生成' : '发送';
    updateSendState();
  }
  function focusInput() { els.input.focus(); }

  /* ---------------- 术数卡片（对话流内） ---------------- */
  function buildToolCard(tools) {
    const row = document.createElement('div');
    row.className = 'message message--assistant';
    row.innerHTML = '<div class="avatar avatar--bot">玄</div><div class="bubble bubble--bot tool-card-host"></div>';
    const host = row.querySelector('.tool-card-host');
    host.innerHTML = (tools || []).map((key) => {
      const m = METHODS.find((x) => x.key === key);
      return m ? '<button class="tool-chip" data-method="' + m.key + '"><span class="emoji">' + m.emoji + '</span>' + m.name + '</button>' : '';
    }).join('');
    return row;
  }

  function openDivination(method) {
    activeMethod = method || 'bazi';
    activeToolKey = activeMethod;
    const m = METHODS.find((x) => x.key === activeMethod);
    if (els.divinationTitle) els.divinationTitle.textContent = m ? (m.emoji + ' ' + m.name) : '术数';
    renderForm(activeMethod);
    els.divinationModal.classList.add('is-show');
  }
  function closeDivination() { els.divinationModal.classList.remove('is-show'); }

  /* ---------------- 设置 ---------------- */
  function renderModelOptions() {
    els.modelOptions.innerHTML = MODELS.map((m) =>
      '<button class="model-option' + (m.key === settings.model ? ' is-selected' : '') + '" data-model="' + m.key + '">' +
      '<span class="model-option__name">' + m.name + '</span>' +
      '<span class="model-option__desc">' + m.desc + '</span></button>'
    ).join('');
  }
  function openSettings() {
    renderModelOptions();
    els.settingsApiKey.value = settings.apiKey || '';
    els.settings.classList.add('is-show');
  }
  function closeSettings() { els.settings.classList.remove('is-show'); }
  function saveSettings() {
    const selected = els.modelOptions.querySelector('.model-option.is-selected');
    settings.model = selected ? selected.dataset.model : 'deepseek-flash';
    settings.apiKey = els.settingsApiKey.value.trim();
    persistSettings();
    els.modelName.textContent = settings.model;
    closeSettings();
  }

  /* ---------------- 主题 ---------------- */
  function currentTheme() { return localStorage.getItem(THEME_KEY) || 'dark'; }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
    els.themeToggle.innerHTML = theme === 'dark' ? ICON.moon : ICON.sun;
    els.themeToggle.title = theme === 'dark' ? '切换为浅色' : '切换为深色';
  }

  /* ---------------- 侧边栏 ---------------- */
  function openSidebar() { els.sidebar.classList.add('is-open'); els.sidebarBackdrop.classList.add('is-open'); }
  function closeSidebar() { els.sidebar.classList.remove('is-open'); els.sidebarBackdrop.classList.remove('is-open'); }

  /* ---------------- 健康检查 ---------------- */
  async function checkHealth() {
    // 免费版 Render 可能正休眠，唤醒需几十秒：延长超时并多次重试，避免误判离线
    let online = false;
    for (let i = 0; i < 4; i++) {
      try {
        await axios.get(API_BASE + '/api/health', { timeout: 15000 });
        online = true;
        break;
      } catch {
        if (i < 3) await new Promise((r) => setTimeout(r, 4000));
      }
    }
    if (online) {
      els.statusText.textContent = '在线';
      els.status.classList.add('is-online');
      els.modelName.textContent = settings.model;
    } else {
      els.statusText.textContent = '离线';
      els.status.classList.remove('is-online');
      els.modelName.textContent = '';
    }
  }

  /* ---------------- 事件绑定 ---------------- */
  function bindEvents() {
    els.send.addEventListener('click', () => {
      if (streaming) stopGeneration(); else sendMessage();
    });
    els.input.addEventListener('input', () => { autoResize(); updateSendState(); });
    els.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.isComposing) {
        e.preventDefault();
        if (e.ctrlKey || e.shiftKey) {
          insertNewline();          // Ctrl+Enter / Shift+Enter 换行
        } else if (!streaming) {
          sendMessage();            // Enter 发送
        }
      }
    });

    els.newChat.addEventListener('click', () => createConversation());
    els.themeToggle.addEventListener('click', () => applyTheme(currentTheme() === 'dark' ? 'light' : 'dark'));

    els.chatList.addEventListener('click', (e) => {
      const item = e.target.closest('.chat-item');
      if (!item) return;
      if (e.target.closest('.chat-item__del')) deleteChat(item.dataset.id);
      else switchChat(item.dataset.id);
    });

    els.messages.addEventListener('click', (e) => {
      const chip = e.target.closest('.suggestion');
      if (chip) { els.input.value = chip.dataset.prompt; autoResize(); updateSendState(); sendMessage(); }
      const tool = e.target.closest('.tool-chip');
      if (tool) openDivination(tool.dataset.method);
    });

    // 双击消息气泡复制该消息内容
    els.messages.addEventListener('dblclick', (e) => {
      const bubble = e.target.closest('.bubble');
      if (!bubble) return;
      const text = bubble.innerText.trim();
      if (text) copyText(text);
    });

    els.sidebarToggle.addEventListener('click', () => els.sidebar.classList.contains('is-open') ? closeSidebar() : openSidebar());
    els.sidebarBackdrop.addEventListener('click', closeSidebar);

    els.divinationClose.addEventListener('click', closeDivination);
    els.divinationModal.addEventListener('click', (e) => { if (e.target === els.divinationModal) closeDivination(); });

    // 设置
    els.settingsToggle.addEventListener('click', openSettings);
    els.settingsClose.addEventListener('click', closeSettings);
    els.settingsSave.addEventListener('click', saveSettings);
    els.modelOptions.addEventListener('click', (e) => {
      const btn = e.target.closest('.model-option');
      if (!btn) return;
      els.modelOptions.querySelectorAll('.model-option').forEach((b) => b.classList.toggle('is-selected', b === btn));
    });
    els.settings.addEventListener('click', (e) => { if (e.target === els.settings) closeSettings(); });
  }

  /* ---------------- 初始化 ---------------- */
  function init() {
    applyTheme(currentTheme());

    if (window.DOMPurify) {
      window.DOMPurify.addHook('afterSanitizeAttributes', (node) => {
        if (node.tagName === 'A') {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      });
    }

    bindEvents();
    updateSendState();
    checkHealth();

    if (conversations.length === 0) {
      // 空状态下不自动建对话，显示欢迎页；等用户发消息时再创建
      currentId = null;
      messages = [];
      renderChatList();
      renderMessages();
    } else {
      switchChat(conversations[0].id);
    }
  }

  init();
})();
