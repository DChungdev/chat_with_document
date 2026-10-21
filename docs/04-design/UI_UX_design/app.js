/* Prototype "Chat với tài liệu" — mô phỏng toàn bộ hành vi UI theo UIUX_Blueprint_SDD.md.
   Không có backend: upload, xử lý, streaming, nguồn dẫn đều là dữ liệu giả lập. */
(function () {
  'use strict';

  /* ---------- Cấu hình (UI đọc từ config, không hard-code — DD-09; giá trị là giả định, OQ-008) ---------- */
  const CONFIG = { maxFileSize: 20 * 1024 * 1024, maxFiles: 10, maxQuestionLength: 2000, noticeVersion: 'v0.1' };

  /* ---------- Tiện ích ---------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ic = (n) => `<svg class="icon" aria-hidden="true"><use href="#i-${n}"/></svg>`;
  const uid = (() => { let n = 0; return (p) => `${p}${++n}`; })();
  const fmtSize = (b) => (b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB');
  const fmtAge = (t) => {
    const m = Math.floor((Date.now() - t) / 60000);
    return m < 1 ? 'vừa xong' : m < 60 ? `${m} phút trước` : `${Math.floor(m / 60)} giờ trước`;
  };

  /* ---------- Telemetry: một lớp duy nhất + danh sách thuộc tính cho phép (DD-08, PRD 5.2) ---------- */
  const ALLOWED = {
    session_started: ['entry_source'], data_notice_accepted: ['notice_version'],
    upload_started: ['file_size', 'file_index'], upload_succeeded: ['file_size', 'duration_ms'], upload_failed: ['file_size', 'error_code'],
    document_ready: ['page_count', 'processing_ms'], document_processing_failed: ['error_code'], document_deleted: ['document_age_days'],
    question_submitted: ['question_length', 'docs_selected_count'], answer_first_token: ['latency_ms'],
    answer_completed: ['total_ms', 'citation_count', 'grounded'], answer_failed: ['error_code', 'stage', 'elapsed_ms'], answer_stopped: ['elapsed_ms'],
    citation_opened: ['citation_index'], answer_feedback: ['rating', 'reason_code'], copy_answer: ['answer_id'],
    task_marked_done: ['task_id', 'elapsed_ms', 'success'],
  };
  const telLog = [];
  function emit(name, props = {}) {
    const allow = ALLOWED[name];
    const clean = {}; const blocked = [];
    Object.keys(props).forEach((k) => (allow && allow.includes(k) ? (clean[k] = props[k]) : blocked.push(k)));
    telLog.push({ t: new Date().toLocaleTimeString('vi-VN'), name: allow ? name : name + ' (không hợp lệ)', clean, blocked });
    drawTel();
  }
  function drawTel() {
    $('#tel-log').innerHTML = telLog.slice(-40).map((e) =>
      `<div class="${e.blocked.length ? 'blocked' : ''}">${e.t}  ${esc(e.name)} ${esc(JSON.stringify(e.clean))}${e.blocked.length ? '  ⛔ chặn: ' + esc(e.blocked.join(',')) : ''}</div>`).join('');
    $('#tel-log').scrollTop = 1e9;
  }

  /* ---------- Dữ liệu giả lập ---------- */
  const KB = [
    { keys: ['thanh toán', 'điều khoản', 'hạn thanh'], text: 'Theo tài liệu, thanh toán được thực hiện trong vòng 30 ngày kể từ ngày xuất hóa đơn. Nếu thanh toán chậm, bên mua chịu lãi 0,05% mỗi ngày trên số tiền chậm trả.',
      cites: [{ d: 0, page: 4, snippet: 'Thanh toán trong 30 ngày kể từ ngày xuất hóa đơn hợp lệ. Mọi khoản thanh toán thực hiện bằng chuyển khoản.' }, { d: 1, page: 2, snippet: 'Trường hợp chậm thanh toán, bên mua chịu lãi suất 0,05% mỗi ngày trên số tiền chậm trả.' }] },
    { keys: ['bảo hành', 'bao hanh'], text: 'Thiết bị được bảo hành 24 tháng kể từ ngày nghiệm thu. Bảo hành không áp dụng cho hư hỏng do sử dụng sai hướng dẫn.',
      cites: [{ d: 0, page: 7, snippet: 'Thời gian bảo hành là 24 tháng kể từ ngày nghiệm thu, không bao gồm hư hỏng do sử dụng sai hướng dẫn.' }] },
    { keys: ['giá', 'báo giá', 'chi phí', 'bao nhiêu'], text: 'Tổng giá trị báo giá là 1.250.000.000 VND, chưa gồm VAT 10%. Giá có hiệu lực trong 60 ngày.',
      cites: [{ d: 0, page: 2, snippet: 'Tổng giá trị: 1.250.000.000 VND (chưa bao gồm thuế GTGT 10%).' }, { d: 0, page: 3, snippet: 'Báo giá có hiệu lực trong 60 ngày kể từ ngày phát hành.' }] },
  ];
  const NOT_FOUND = 'Tôi không tìm thấy thông tin này trong các tài liệu đã tải lên. Hãy thử diễn đạt khác hoặc tải thêm tài liệu liên quan.';
  const SUGGESTIONS = ['Điều khoản thanh toán là gì?', 'Thời gian bảo hành bao lâu?', 'Tổng giá trị báo giá là bao nhiêu?'];

  /* ---------- State ---------- */
  const state = {
    noticeAccepted: false, killSwitch: false, trial: false,
    docs: [], messages: [], sourceOpen: false, active: null, sessionExpired: false,
  };
  const timers = new Map(); // id -> {handles:[]}
  let pendingDelete = null; let lastTrigger = null;

  const readyDocs = () => state.docs.filter((d) => d.status === 'ready');
  const selectedReady = () => readyDocs().filter((d) => d.selected);
  const streamingMsg = () => state.messages.find((m) => m.role === 'ai' && (m.status === 'sending' || m.status === 'streaming'));

  /* ---------- Toast / NotificationCenter ---------- */
  function toast(kind, msg, sticky) {
    const el = document.createElement('div');
    el.className = `toast alert alert-${kind}`;
    el.innerHTML = `${ic(kind === 'success' ? 'check' : kind === 'info' ? 'info' : 'alert')}<span class="grow">${esc(msg)}</span><button class="btn btn-ghost btn-icon btn-sm" aria-label="Đóng thông báo">${ic('x')}</button>`;
    $('.btn', el).onclick = () => el.remove();
    $('#toasts').appendChild(el);
    if (kind === 'success' || (kind === 'info' && !sticky)) setTimeout(() => el.remove(), 5000); // thành công tự ẩn sau 5s; lỗi giữ lại
  }

  /* ---------- Tài liệu ---------- */
  const STATUS = {
    uploading: (d) => ({ cls: 'info', icon: 'upload', text: `Đang tải lên… (${d.progress}%)` }),
    upload_failed: () => ({ cls: 'danger', icon: 'alert', text: 'Tải thất bại' }),
    processing: () => ({ cls: 'warning', icon: 'clock', text: 'Đang xử lý' }),
    ready: () => ({ cls: 'success', icon: 'check', text: 'Sẵn sàng' }),
    error: (d) => ({ cls: 'danger', icon: 'x', text: `Lỗi: ${d.errorMsg}` }),
  };

  function renderDocs() {
    const focus = document.activeElement && document.activeElement.dataset && document.activeElement.dataset.act
      ? { id: document.activeElement.dataset.id, act: document.activeElement.dataset.act } : null;
    $('#doc-count').textContent = state.docs.length;
    $('#doc-empty').hidden = state.docs.length > 0;
    $('#doc-list').innerHTML = state.docs.map((d) => {
      const s = STATUS[d.status](d);
      const ready = d.status === 'ready';
      const bar = d.status === 'uploading'
        ? `<div class="progress" role="progressbar" aria-label="Tiến trình tải ${esc(d.name)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${d.progress}"><span style="width:${d.progress}%"></span></div>`
        : d.status === 'processing' ? '<div class="progress indeterminate" aria-hidden="true"><span></span></div>' : '';
      const act = (a, label, cls = '') => `<button class="btn btn-sm ${cls}" data-act="${a}" data-id="${d.id}">${label}</button>`;
      const actions = d.status === 'uploading' ? act('cancel', 'Hủy')
        : d.status === 'upload_failed' ? act('retry', ic('refresh') + 'Thử lại') + act('delete', ic('trash') + 'Xóa')
        : d.status === 'processing' ? '' : act('delete', ic('trash') + 'Xóa');
      return `<li class="doc-item">
        <span class="checkbox-hit"><input type="checkbox" class="checkbox" data-act="select" data-id="${d.id}" ${ready ? '' : 'disabled'} ${ready && d.selected ? 'checked' : ''} aria-label="Dùng ${esc(d.name)} để hỏi đáp"></span>
        <div class="doc-main">
          <span class="doc-name" title="${esc(d.name)}">${esc(d.name)}</span>
          <span class="doc-meta">${fmtSize(d.size)} · ${fmtAge(d.uploadedAt)}</span>
          <span><span class="badge badge-${s.cls}">${ic(s.icon)}${esc(s.text)}</span></span>
          ${bar}
          <div class="doc-actions">${actions}</div>
        </div></li>`;
    }).join('');
    if (focus) { const el = $(`[data-act="${focus.act}"][data-id="${focus.id}"]`); if (el) el.focus(); }
    renderComposer();
    renderMessages(false);
  }

  function setTimers(id, fn) { const t = timers.get(id) || []; t.push(fn); timers.set(id, t); }
  function clearTimers(id) { (timers.get(id) || []).forEach((h) => { clearTimeout(h); clearInterval(h); }); timers.delete(id); }

  function startUpload(d) {
    d.status = 'uploading'; d.progress = 0; d.startedAt = Date.now();
    renderDocs();
    const iv = setInterval(() => {
      d.progress = Math.min(100, d.progress + 20);
      if (d.progress >= 100) {
        clearInterval(iv);
        d.status = 'processing';
        emit('upload_succeeded', { file_size: d.size, duration_ms: Date.now() - d.startedAt });
        const pt = Date.now();
        setTimers(d.id, setTimeout(() => {
          if (/loi|error|mat.?khau/i.test(d.name)) {
            d.status = 'error'; d.errorMsg = 'PDF có mật khẩu';
            emit('document_processing_failed', { error_code: 'PDF_ENCRYPTED' });
            toast('danger', `Không xử lý được “${d.name}”: PDF có mật khẩu. Hãy gỡ mật khẩu rồi tải lại.`, true);
          } else {
            d.status = 'ready'; d.selected = true; d.pages = 12;
            emit('document_ready', { page_count: 12, processing_ms: Date.now() - pt });
            toast('success', `“${d.name}” đã sẵn sàng.`);
          }
          renderDocs();
        }, 2200));
      }
      renderDocs();
    }, 350);
    setTimers(d.id, iv);
  }

  function addFiles(files) {
    if (!state.noticeAccepted) { toast('warning', 'Hãy xác nhận thông báo dữ liệu trước khi tải tài liệu.'); return; }
    Array.from(files).forEach((f, i) => {
      if (!/\.pdf$/i.test(f.name) && f.type !== 'application/pdf') { toast('danger', `“${f.name}” không phải PDF. Hiện chỉ hỗ trợ tệp .pdf.`, true); return; }
      if (f.size > CONFIG.maxFileSize) { toast('danger', `“${f.name}” vượt giới hạn ${fmtSize(CONFIG.maxFileSize)}. Hãy chọn tệp nhỏ hơn.`, true); return; }
      if (state.docs.length >= CONFIG.maxFiles) { toast('danger', `Đã đạt tối đa ${CONFIG.maxFiles} tài liệu. Xóa bớt để tải thêm.`, true); return; }
      const d = { id: uid('d'), name: f.name, size: f.size, uploadedAt: Date.now(), status: 'uploading', progress: 0, selected: false };
      state.docs.unshift(d);
      emit('upload_started', { file_size: f.size, file_index: i });
      startUpload(d);
    });
  }

  function askDelete(id) {
    const d = state.docs.find((x) => x.id === id); if (!d) return;
    pendingDelete = d; lastTrigger = document.activeElement;
    $('#del-name').textContent = d.name;
    $('#dlg-delete').showModal();
  }

  /* ---------- Composer ---------- */
  function composerState() {
    const text = $('#composer-input').value;
    if (!state.noticeAccepted) return { off: true, reason: 'Xác nhận thông báo dữ liệu để bắt đầu' };
    if (state.killSwitch) return { off: true, reason: 'Tính năng hỏi đáp tạm thời không khả dụng' };
    if (!readyDocs().length) return { off: true, reason: 'Tải ít nhất 1 PDF và chờ ở trạng thái Sẵn sàng' };
    if (!selectedReady().length) return { off: true, reason: 'Chọn ít nhất 1 tài liệu để hỏi' };
    if (streamingMsg()) return { stop: true, reason: 'Đang tạo câu trả lời…', neutral: true };
    if (!text.trim()) return { sendOff: true };
    if (text.length > CONFIG.maxQuestionLength) return { sendOff: true, reason: `Tối đa ${CONFIG.maxQuestionLength} ký tự` };
    return {};
  }
  function renderComposer() {
    const c = composerState(); const input = $('#composer-input'); const btn = $('#btn-send');
    input.disabled = !!c.off;
    btn.disabled = !!(c.off || c.sendOff);
    btn.innerHTML = c.stop ? `${ic('stop')}<span class="hide-sm">Dừng</span>` : `${ic('send')}<span class="hide-sm">Gửi</span>`;
    btn.setAttribute('aria-label', c.stop ? 'Dừng tạo câu trả lời' : 'Gửi câu hỏi');
    if (c.stop) btn.disabled = false;
    const hint = $('#composer-hint'); hint.textContent = c.reason || '';
    hint.style.color = c.neutral ? 'var(--text-muted)' : '';
    $('#composer-count').textContent = `${input.value.length}/${CONFIG.maxQuestionLength} · Shift+Enter xuống dòng`;
    $('#trial-bar').hidden = !state.trial;
    $('#global-banner').innerHTML = state.killSwitch
      ? `<div class="alert alert-danger">${ic('alert')}<span class="grow"><strong>Hỏi đáp tạm thời không khả dụng.</strong> Chúng tôi đang khắc phục. Tài liệu của bạn vẫn được giữ nguyên.</span></div>` : '';
    $('#btn-upload').disabled = !state.noticeAccepted;
    $('#btn-upload-empty').disabled = !state.noticeAccepted;
    $('#dropzone').hidden = !state.noticeAccepted;
    $('#doc-limit').innerHTML = `Giới hạn: ≤ ${fmtSize(CONFIG.maxFileSize)}/tệp, tối đa ${CONFIG.maxFiles} tệp <span class="tbd">TBD: OQ-008</span>`;
  }
  function autoGrow() { const i = $('#composer-input'); i.style.height = 'auto'; i.style.height = Math.min(i.scrollHeight, 160) + 'px'; }

  /* ---------- Chat ---------- */
  function renderMessages(stick) {
    const box = $('#messages');
    const atBottom = stick !== false && box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    if (!state.messages.length) {
      box.innerHTML = readyDocs().length
        ? `<div class="empty"><div class="empty-art">${ic('sparkle')}</div><h3>Bạn muốn hỏi gì?</h3><p>Chọn một câu hỏi mẫu hoặc tự nhập câu hỏi.</p>
           <div class="suggestions">${SUGGESTIONS.map((s) => `<button class="btn suggestion" data-act="suggest">${esc(s)}</button>`).join('')}</div></div>`
        : `<div class="empty"><div class="empty-art">${ic('file')}</div><h3>Hãy tải PDF để bắt đầu</h3><p>Sau khi tài liệu ở trạng thái “Sẵn sàng”, bạn có thể đặt câu hỏi bằng tiếng Việt và nhận câu trả lời kèm nguồn dẫn.</p></div>`;
      return;
    }
    box.innerHTML = state.messages.map(msgHtml).join('');
    if (atBottom) box.scrollTop = box.scrollHeight;
  }

  function msgHtml(m) {
    if (m.role === 'user') return `<div class="msg msg-user"><div class="msg-head">Bạn</div><div class="bubble">${esc(m.text)}</div></div>`;
    const live = m.status === 'sending' || m.status === 'streaming';
    let body;
    if (m.status === 'sending') body = '<div class="skeleton" style="width:90%;margin-bottom:8px"></div><div class="skeleton" style="width:65%"></div>';
    else body = esc(m.text) + (m.status === 'streaming' ? '<span class="cursor" aria-hidden="true"></span>' : '');
    let status = '';
    if (live) status = `<div class="msg-status"><span class="spinner" aria-hidden="true"></span>${m.status === 'sending' ? 'Đang tìm trong tài liệu…' : 'Đang tạo câu trả lời…'}</div>`;
    if (m.status === 'interrupted') status = `<div class="msg-status warning">${ic('alert')}Bị gián đoạn — phần đã nhận được vẫn được giữ lại. <button class="btn btn-sm" data-act="regen" data-id="${m.id}">${ic('refresh')}Tạo lại</button></div>`;
    if (m.status === 'failed') status = `<div class="msg-status danger">${ic('alert')}Chưa thể tạo câu trả lời lúc này. Câu hỏi của bạn vẫn được giữ. <button class="btn btn-sm" data-act="regen" data-id="${m.id}">${ic('refresh')}Thử lại</button></div>`;
    if (m.status === 'stopped') status = `<div class="msg-status">${ic('stop')}Đã dừng. <button class="btn btn-sm" data-act="regen" data-id="${m.id}">${ic('refresh')}Hỏi lại</button></div>`;
    let extra = '';
    if (m.status === 'complete') {
      const chips = (m.citations || []).map((c, i) => {
        const valid = state.docs.some((d) => d.id === c.documentId);
        const open = state.sourceOpen && state.active && state.active.msg === m.id && state.active.idx === i;
        return `<button class="chip ${valid ? '' : 'invalid'}" data-act="cite" data-id="${m.id}" data-idx="${i}" aria-expanded="${open}" aria-controls="panel-source">${ic('file')}${esc(c.documentName)} · tr.${c.page}</button>`;
      }).join('');
      extra = (chips ? `<div class="chips" aria-label="Nguồn dẫn">${chips}</div>` : '') +
        `<div class="answer-actions">
          <button class="btn btn-sm btn-ghost" data-act="copy" data-id="${m.id}">${ic('copy')}Sao chép</button>
          <button class="btn btn-sm btn-ghost btn-icon" data-act="rate" data-rate="up" data-id="${m.id}" aria-pressed="${m.feedback === 'up'}" aria-label="Hữu ích">${ic('up')}</button>
          <button class="btn btn-sm btn-ghost btn-icon" data-act="rate" data-rate="down" data-id="${m.id}" aria-pressed="${m.feedback === 'down'}" aria-label="Không hữu ích">${ic('down')}</button>
        </div>`;
    }
    return `<div class="msg msg-ai" data-id="${m.id}">
      <div class="msg-head">${ic('sparkle')}Trợ lý AI <span class="badge badge-neutral">Do AI tạo</span></div>
      <div class="bubble ${m.status === 'complete' && m.grounded === false ? 'not-grounded' : ''}" id="b-${m.id}">${body}</div>
      ${status}${extra}</div>`;
  }

  function ask(text) {
    const q = text.trim(); if (!q) return;
    state.messages.push({ id: uid('m'), role: 'user', text: q });
    const ai = { id: uid('m'), role: 'ai', question: q, text: '', status: 'sending', citations: [], grounded: true, feedback: null };
    state.messages.push(ai);
    emit('question_submitted', { question_length: q.length, docs_selected_count: selectedReady().length });
    $('#composer-input').value = ''; autoGrow();
    run(ai); renderMessages(true); renderComposer();
  }

  function pickAnswer(q) {
    const l = q.toLowerCase();
    const hit = KB.find((k) => k.keys.some((w) => l.includes(w)));
    if (!hit) return { text: NOT_FOUND, cites: [], grounded: false };
    const docs = selectedReady();
    return { text: hit.text, grounded: true, cites: hit.cites.map((c) => { const d = docs[c.d % docs.length]; return { documentId: d.id, documentName: d.name, page: c.page, snippet: c.snippet, valid: true }; }) };
  }

  function run(ai) {
    clearTimers(ai.id);
    const sim = $('#sim-mode').value; $('#sim-mode').value = 'ok'; // chỉ áp dụng cho một lần hỏi
    ai.status = 'sending'; ai.text = ''; ai.citations = [];
    const t0 = Date.now(); const ans = pickAnswer(ai.question);
    const tokens = ans.text.split(/(\s+)/);
    setTimers(ai.id, setTimeout(() => {
      if (sim === 'fail') {
        ai.status = 'failed'; emit('answer_failed', { error_code: 'AI_TIMEOUT', stage: 'generation', elapsed_ms: Date.now() - t0 });
        renderMessages(true); renderComposer(); return;
      }
      ai.status = 'streaming'; emit('answer_first_token', { latency_ms: Date.now() - t0 });
      renderMessages(true); renderComposer();
      let i = 0;
      const iv = setInterval(() => {
        i += 2; ai.text = tokens.slice(0, i).join('');
        if (sim === 'interrupt' && i > tokens.length * 0.4) {
          clearInterval(iv); ai.status = 'interrupted';
          emit('answer_failed', { error_code: 'NETWORK_LOST', stage: 'streaming', elapsed_ms: Date.now() - t0 });
          renderMessages(true); renderComposer(); toast('warning', 'Kết nối bị gián đoạn. Bạn có thể bấm “Tạo lại”.'); return;
        }
        if (i >= tokens.length) {
          clearInterval(iv); ai.text = ans.text; ai.status = 'complete'; ai.citations = ans.cites; ai.grounded = ans.grounded;
          emit('answer_completed', { total_ms: Date.now() - t0, citation_count: ans.cites.length, grounded: ans.grounded });
          renderMessages(true); renderComposer(); return;
        }
        const b = $('#b-' + ai.id); // cập nhật tăng dần, không dựng lại cả danh sách
        if (b) { b.innerHTML = esc(ai.text) + '<span class="cursor" aria-hidden="true"></span>'; const box = $('#messages'); if (box.scrollHeight - box.scrollTop - box.clientHeight < 120) box.scrollTop = box.scrollHeight; }
      }, 70);
      setTimers(ai.id, iv);
    }, 700));
  }

  function stop() {
    const ai = streamingMsg(); if (!ai) return;
    clearTimers(ai.id); ai.status = 'stopped';
    emit('answer_stopped', { elapsed_ms: 0 });
    renderMessages(true); renderComposer();
  }

  /* ---------- Nguồn dẫn (SourcePanel) ---------- */
  function openSource(msgId, idx, trigger) {
    const m = state.messages.find((x) => x.id === msgId); const c = m && m.citations[idx]; if (!c) return;
    lastTrigger = trigger; state.sourceOpen = true; state.active = { msg: msgId, idx };
    $('#workspace').classList.add('source-open'); $('#panel-source').setAttribute('aria-hidden', 'false');
    $('#source-body').innerHTML = '<div class="skeleton" style="width:50%"></div><div class="skeleton" style="height:64px"></div>';
    emit('citation_opened', { citation_index: idx });
    renderMessages(false);
    setTimeout(() => {
      const valid = state.docs.some((d) => d.id === c.documentId);
      $('#source-body').innerHTML = valid
        ? `<div class="source-meta"><span class="badge badge-info">${ic('file')}${esc(c.documentName)}</span><span class="badge badge-neutral">Trang ${c.page}</span></div>
           <blockquote class="source-quote">“${esc(c.snippet)}”</blockquote>
           <p class="muted" style="font-size:var(--text-sm)">Đoạn gốc trích từ tài liệu bạn đã tải lên. Đối chiếu với câu trả lời trước khi sử dụng.</p>`
        : `<div class="alert alert-warning">${ic('alert')}<span class="grow"><strong>Nguồn không còn khả dụng.</strong> Tài liệu “${esc(c.documentName)}” đã bị xóa. Tải lại tài liệu và hỏi lại nếu cần kiểm chứng.</span></div>`;
    }, 250);
    $('#btn-close-source').focus();
  }
  function closeSource() {
    if (!state.sourceOpen) return;
    state.sourceOpen = false; state.active = null;
    $('#workspace').classList.remove('source-open'); $('#panel-source').setAttribute('aria-hidden', 'true');
    renderMessages(false);
    if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus();
    else { const first = $('[data-act="cite"]'); if (first) first.focus(); }
  }

  /* ---------- Thông báo dữ liệu (SCR-01) ---------- */
  function openNotice(review) {
    const dlg = $('#dlg-notice'); const chk = $('#notice-check');
    chk.checked = !!review; chk.disabled = !!review;
    $('#notice-ok').hidden = !!review; $('#notice-ok').disabled = !review && !chk.checked;
    $('#notice-close').hidden = !review;
    if (!dlg.open) dlg.showModal();
  }

  /* ---------- Kịch bản demo ---------- */
  function sample(status, name, size, extra = {}) { return Object.assign({ id: uid('d'), name, size, uploadedAt: Date.now() - 120000, status, progress: 100, selected: status === 'ready' }, extra); }
  function resetAll() {
    timers.forEach((_, id) => clearTimers(id));
    $$('dialog[open]').forEach((d) => d.close());
    state.killSwitch = false; state.sourceOpen = false; state.active = null; state.docs = []; state.messages = [];
    $('#workspace').classList.remove('source-open'); $('#panel-source').setAttribute('aria-hidden', 'true');
    $('#composer-input').value = ''; $('#toasts').innerHTML = ''; closeDrawer();
  }
  function conversation() {
    const [a, b] = readyDocs();
    state.messages = [
      { id: uid('m'), role: 'user', text: 'Điều khoản thanh toán là gì?' },
      { id: uid('m'), role: 'ai', question: 'Điều khoản thanh toán là gì?', status: 'complete', grounded: true, feedback: null, text: KB[0].text,
        citations: [{ documentId: a.id, documentName: a.name, page: 4, snippet: KB[0].cites[0].snippet, valid: true }, { documentId: (b || a).id, documentName: (b || a).name, page: 2, snippet: KB[0].cites[1].snippet, valid: true }] },
    ];
  }
  function scenario(n) {
    resetAll();
    document.querySelectorAll('[data-scr]').forEach((b) => b.classList.toggle('active', b.dataset.scr === n));
    if (n === '01') { state.noticeAccepted = false; renderDocs(); openNotice(false); return; }
    state.noticeAccepted = true;
    if (n === '02') { renderDocs(); return; }
    if (n === '03') {
      state.docs = [sample('ready', 'baogia.pdf', 1258000), sample('uploading', 'hopdong.pdf', 3400000, { progress: 60 }), sample('error', 'catalog.pdf', 5200000, { errorMsg: 'PDF có mật khẩu' })];
      renderDocs(); return;
    }
    state.docs = [sample('ready', 'baogia.pdf', 1258000), sample('ready', 'hopdong.pdf', 3400000), sample('error', 'catalog.pdf', 5200000, { errorMsg: 'PDF có mật khẩu' })];
    if (n === '04' || n === '05' || n === '06') conversation();
    if (n === '07') { $('#composer-input').value = 'Thời hạn bảo hành của thiết bị là bao lâu'; }
    if (n === '08') state.killSwitch = true;
    renderDocs(); renderComposer(); autoGrow();
    if (n === '05') openSource(state.messages[1].id, 0, $('[data-act="cite"]'));
    if (n === '06') askDelete(state.docs[1].id);
    if (n === '07') { $('#dlg-session').showModal(); }
  }

  /* ---------- Drawer (< 1024px) ---------- */
  function openDrawer() { $('#panel-docs').classList.add('open'); $('#scrim').hidden = false; $('#btn-menu').setAttribute('aria-expanded', 'true'); }
  function closeDrawer() { $('#panel-docs').classList.remove('open'); $('#scrim').hidden = true; $('#btn-menu').setAttribute('aria-expanded', 'false'); }

  /* ---------- Sự kiện ---------- */
  $('#btn-upload').onclick = $('#btn-upload-empty').onclick = () => $('#file-input').click();
  $('#file-input').onchange = (e) => { addFiles(e.target.files); e.target.value = ''; };
  const dz = $('#dropzone');
  ['dragenter', 'dragover'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('drag'); }));
  ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('drag'); }));
  dz.addEventListener('drop', (e) => addFiles(e.dataTransfer.files));

  $('#doc-list').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b || b.dataset.act === 'select') return;
    const d = state.docs.find((x) => x.id === b.dataset.id); if (!d) return;
    if (b.dataset.act === 'delete') askDelete(d.id);
    if (b.dataset.act === 'cancel') { clearTimers(d.id); state.docs = state.docs.filter((x) => x !== d); renderDocs(); toast('info', `Đã hủy tải “${d.name}”.`); }
    if (b.dataset.act === 'retry') startUpload(d);
  });
  $('#doc-list').addEventListener('change', (e) => {
    const b = e.target.closest('[data-act="select"]'); if (!b) return;
    const d = state.docs.find((x) => x.id === b.dataset.id); if (d) { d.selected = b.checked; renderComposer(); }
  });

  $('#del-cancel').onclick = () => { $('#dlg-delete').close(); pendingDelete = null; };
  $('#del-ok').onclick = () => {
    const d = pendingDelete; $('#dlg-delete').close(); if (!d) return;
    clearTimers(d.id); state.docs = state.docs.filter((x) => x !== d);
    emit('document_deleted', { document_age_days: Math.floor((Date.now() - d.uploadedAt) / 86400000) });
    renderDocs(); toast('success', `Đã xóa “${d.name}”.`); pendingDelete = null;
    const t = $('#btn-upload'); if (t) t.focus();
  };

  $('#messages').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    const m = state.messages.find((x) => x.id === b.dataset.id);
    switch (b.dataset.act) {
      case 'suggest': $('#composer-input').value = b.textContent; renderComposer(); ask(b.textContent); break;
      case 'cite': state.sourceOpen && state.active && state.active.msg === m.id && state.active.idx === +b.dataset.idx ? closeSource() : openSource(m.id, +b.dataset.idx, b); break;
      case 'regen': if (!streamingMsg()) { run(m); renderMessages(true); renderComposer(); } break;
      case 'copy':
        try { navigator.clipboard.writeText(m.text).then(() => toast('success', 'Đã sao chép câu trả lời.'), () => toast('danger', 'Không sao chép được. Hãy chọn và sao chép thủ công.', true)); }
        catch (_) { toast('danger', 'Không sao chép được. Hãy chọn và sao chép thủ công.', true); }
        emit('copy_answer', { answer_id: m.id }); break;
      case 'rate': {
        const r = b.dataset.rate; m.feedback = m.feedback === r ? null : r;
        if (m.feedback) { emit('answer_feedback', { rating: m.feedback }); toast('success', 'Cảm ơn phản hồi của bạn.'); }
        renderMessages(false); const again = $(`[data-act="rate"][data-rate="${r}"][data-id="${m.id}"]`); if (again) again.focus(); break;
      }
    }
  });
  $('#messages').addEventListener('scroll', () => { const b = $('#messages'); $('#btn-scroll-down').hidden = b.scrollHeight - b.scrollTop - b.clientHeight < 120; });
  $('#btn-scroll-down').onclick = () => { const b = $('#messages'); b.scrollTop = b.scrollHeight; };

  const input = $('#composer-input');
  input.addEventListener('input', () => { renderComposer(); autoGrow(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { // isComposing: không gửi nhầm khi đang gõ dấu tiếng Việt (IME)
      e.preventDefault(); const c = composerState(); if (!c.off && !c.sendOff && !c.stop) ask(input.value);
    }
  });
  $('#btn-send').onclick = () => { const c = composerState(); if (c.stop) return stop(); if (!c.off && !c.sendOff) ask(input.value); };
  $('#btn-task-done').onclick = () => { emit('task_marked_done', { task_id: 'T-1', elapsed_ms: 0, success: true }); toast('success', 'Đã ghi nhận. Cảm ơn bạn!'); };

  $('#btn-close-source').onclick = closeSource;
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && state.sourceOpen && !$('dialog[open]')) closeSource(); });

  $('#btn-menu').onclick = () => ($('#panel-docs').classList.contains('open') ? closeDrawer() : openDrawer());
  $('#scrim').onclick = closeDrawer;

  $('#btn-notice').onclick = () => openNotice(state.noticeAccepted);
  $('#notice-check').onchange = (e) => { $('#notice-ok').disabled = !e.target.checked; };
  $('#notice-ok').onclick = () => {
    state.noticeAccepted = true; $('#dlg-notice').close();
    emit('data_notice_accepted', { notice_version: CONFIG.noticeVersion });
    renderDocs(); $('#btn-upload').focus();
  };
  $('#notice-close').onclick = () => $('#dlg-notice').close();
  $('#dlg-notice').addEventListener('cancel', (e) => { if (!state.noticeAccepted) e.preventDefault(); }); // cổng chặn (DD-06)
  $('#dlg-session').addEventListener('cancel', (e) => e.preventDefault());
  $('#ses-ok').onclick = () => { $('#dlg-session').close(); toast('success', 'Đã đăng nhập lại. Câu hỏi đang soạn được khôi phục.'); input.focus(); };

  $$('[data-scr]').forEach((b) => (b.onclick = () => scenario(b.dataset.scr)));
  $('#trial-toggle').onchange = (e) => { state.trial = e.target.checked; renderComposer(); };
  $('#btn-tel').onclick = () => { const l = $('#tel-log'); l.hidden = !l.hidden; drawTel(); };

  /* ---------- Khởi động ---------- */
  setInterval(() => { if (state.docs.length) { const f = document.activeElement; if (!f || !f.closest('#doc-list')) renderDocs(); } }, 60000); // làm mới "x phút trước"
  emit('session_started', { entry_source: 'direct' });
  const hash = (location.hash.match(/SCR-(0[1-8])/) || [])[1];
  scenario(hash || '01');
})();
