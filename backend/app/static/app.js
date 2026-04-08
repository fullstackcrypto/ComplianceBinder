const API = '';
let token = localStorage.getItem('cb_token') || '';
let currentBinderId = null;
let currentEmail = localStorage.getItem('cb_email') || '';

// UI state
let allBinders = [];
let allTasks = [];
let allDocs = [];
let taskFilter = 'open'; // open | all
let activeTab = 'overview';

const els = {
  authMsg: () => document.getElementById('authMsg'),
  toast: () => document.getElementById('toast'),
  binderList: () => document.getElementById('binderList'),
  binderMeta: () => document.getElementById('binderMeta'),
  stats: () => document.getElementById('stats'),
  nextStep: () => document.getElementById('nextStep'),
  taskList: () => document.getElementById('taskList'),
  docList: () => document.getElementById('docList'),
  binderSearch: () => document.getElementById('binderSearch'),
  dropzone: () => document.getElementById('dropzone'),
};

function toast(msg, isError = false) {
  const t = els.toast();
  t.textContent = msg;
  t.style.borderColor = isError ? 'rgba(255, 90, 106, 0.45)' : 'var(--border)';
  t.classList.remove('hidden');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => t.classList.add('hidden'), 2400);
}

function setMsg(el, msg, isError=false) {
  el.textContent = msg;
  el.style.color = isError ? 'var(--danger)' : 'var(--muted)';
}

function authHeaders() {
  return { Authorization: `Bearer ${token}` };
}

async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, options);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error((txt || res.statusText || 'Request failed').slice(0, 500));
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

function showApp() {
  document.getElementById('auth').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('who').textContent = currentEmail;
}

function showAuth() {
  document.getElementById('auth').classList.remove('hidden');
  document.getElementById('app').classList.add('hidden');
}

async function register() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const msg = document.getElementById('authMsg');
  if (!email || !password) return setMsg(msg, 'Enter email and password', true);
  try {
    await apiFetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    setMsg(msg, 'Registered. Now click Login.');
    toast('Registered. Now login.');
  } catch (e) {
    setMsg(msg, e.message, true);
  }
}

async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const msg = document.getElementById('authMsg');
  if (!email || !password) return setMsg(msg, 'Enter email and password', true);

  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);

  try {
    const data = await apiFetch('/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form
    });
    token = data.access_token;
    currentEmail = email;
    localStorage.setItem('cb_token', token);
    localStorage.setItem('cb_email', currentEmail);
    showApp();
    toast('Signed in');
    await refreshBinders();
  } catch (e) {
    setMsg(msg, 'Login failed: ' + (e.message || ''), true);
  }
}

async function refreshBinders() {
  allBinders = await apiFetch('/binders', { headers: authHeaders() });
  renderBinders();
}

function renderBinders() {
  const list = els.binderList();
  const q = (els.binderSearch()?.value || '').trim().toLowerCase();
  list.innerHTML = '';
  const filtered = allBinders.filter(b => !q || b.name.toLowerCase().includes(q) || b.industry.toLowerCase().includes(q));

  if (filtered.length === 0) {
    const empty = document.createElement('li');
    empty.innerHTML = `<div class="meta">No binders match your search.</div>`;
    list.appendChild(empty);
    return;
  }

  filtered.forEach(b => {
    const li = document.createElement('li');
    li.className = b.id === currentBinderId ? 'selected' : '';
    li.innerHTML = `
      <div><strong>${escapeHtml(b.name)}</strong> <span class="meta">(${escapeHtml(b.industry)})</span></div>
    `;
    li.style.cursor = 'pointer';
    li.onclick = () => selectBinder(b.id, b.name, b.industry);
    list.appendChild(li);
  });
}

function escapeHtml(s) {
  return (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

async function createBinder() {
  const name = document.getElementById('binderName').value.trim();
  const industry = document.getElementById('binderIndustry').value;
  if (!name) return;
  await apiFetch('/binders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ name, industry })
  });
  document.getElementById('binderName').value = '';
  toast('Binder created');
  await refreshBinders();
}

async function selectBinder(id, name, industry='') {
  currentBinderId = id;
  document.getElementById('binderTitle').textContent = name;
  document.getElementById('binderActions').classList.remove('hidden');
  els.binderMeta().textContent = industry ? `Industry: ${industry}` : '';

  // Default to Overview tab on binder change
  setTab('overview');

  await Promise.all([refreshTasks(), refreshDocs()]);
  renderBinders();
  updateStatsAndNext();
  toast('Binder selected');
}

async function refreshTasks() {
  allTasks = await apiFetch(`/binders/${currentBinderId}/tasks`, { headers: authHeaders() });
  renderTasks();
}

function renderTasks() {
  const list = els.taskList();
  list.innerHTML = '';
  const items = taskFilter === 'open' ? allTasks.filter(t => t.status !== 'done') : allTasks;

  if (items.length === 0) {
    const empty = document.createElement('li');
    empty.innerHTML = `<div class="meta">No tasks here yet.</div>`;
    list.appendChild(empty);
    updateStatsAndNext();
    return;
  }

  items
    .slice()
    .sort((a,b) => (a.due_date||'9999').localeCompare(b.due_date||'9999'))
    .forEach(t => {
      const li = document.createElement('li');
      if (t.is_overdue) li.classList.add('overdue');
      const due = t.due_date ? `Due: ${t.due_date}` : '';
      const done = t.status === 'done';
      const overdueIcon = t.is_overdue ? '⚠️ ' : '';
      li.innerHTML = `
        <div class="row between" style="margin:0; gap: 8px;">
          <div>
            <strong>${done ? '✅' : '⬜'} ${overdueIcon}${escapeHtml(t.title)}</strong>
            <span class="meta">${escapeHtml(due)}</span>
          </div>
          ${done ? '' : `<button class="secondary" data-done="${t.id}">Mark done</button>`}
        </div>
        <div class="meta">${escapeHtml(t.description || '')}</div>
      `;
      list.appendChild(li);
    });

  // wire buttons
  list.querySelectorAll('button[data-done]').forEach(btn => {
    btn.onclick = async () => {
      const id = btn.getAttribute('data-done');
      await apiFetch(`/tasks/${id}/done`, { method: 'POST', headers: authHeaders() });
      toast('Task completed');
      await refreshTasks();
      updateStatsAndNext();
    };
  });

  updateStatsAndNext();
}

async function addTask() {
  const title = document.getElementById('taskTitle').value.trim();
  const description = document.getElementById('taskDesc').value.trim();
  const due_date = document.getElementById('taskDue').value || null;
  if (!title) return;

  await apiFetch(`/binders/${currentBinderId}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ title, description, due_date })
  });

  document.getElementById('taskTitle').value = '';
  document.getElementById('taskDesc').value = '';
  document.getElementById('taskDue').value = '';
  toast('Task added');
  await refreshTasks();
  updateStatsAndNext();
}

async function refreshDocs() {
  allDocs = await apiFetch(`/binders/${currentBinderId}/documents`, { headers: authHeaders() });
  renderDocs();
}

function renderDocs() {
  const list = els.docList();
  list.innerHTML = '';
  const docs = allDocs;
  if (docs.length === 0) {
    const empty = document.createElement('li');
    empty.innerHTML = `<div class="meta">No documents uploaded yet.</div>`;
    list.appendChild(empty);
    updateStatsAndNext();
    return;
  }
  docs.forEach(d => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = d.original_name;
    a.onclick = async (e) => {
      e.preventDefault();
      // download via authenticated fetch
      const res = await fetch(`/documents/${d.id}/download`, { headers: authHeaders() });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const tmp = document.createElement('a');
      tmp.href = url;
      tmp.download = d.original_name;
      tmp.click();
      URL.revokeObjectURL(url);
    };
    li.appendChild(a);
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = d.note || '';
    li.appendChild(meta);
    list.appendChild(li);
  });
  updateStatsAndNext();
}

async function uploadDoc() {
  const file = document.getElementById('docFile').files[0];
  const note = document.getElementById('docNote').value.trim();
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  fd.append('note', note);

  await apiFetch(`/binders/${currentBinderId}/documents`, {
    method: 'POST',
    headers: authHeaders(),
    body: fd
  });

  document.getElementById('docFile').value = '';
  document.getElementById('docNote').value = '';
  toast('Uploaded');
  await refreshDocs();
  updateStatsAndNext();
}

function logout() {
  token = '';
  currentBinderId = null;
  localStorage.removeItem('cb_token');
  localStorage.removeItem('cb_email');
  showAuth();
}

function setTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
  document.querySelectorAll('.tabPanel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`tab-${tabName}`)?.classList.remove('hidden');
}

async function openReport() {
  const html = await apiFetch(`/binders/${currentBinderId}/report`, { headers: authHeaders() });
  const w = window.open('', '_blank');
  w.document.open();
  w.document.write(html);
  w.document.close();
}

async function copyReportHtml() {
  const html = await apiFetch(`/binders/${currentBinderId}/report`, { headers: authHeaders() });
  await navigator.clipboard.writeText(html);
  toast('Report HTML copied');
}

function updateStatsAndNext() {
  const open = allTasks.filter(t => t.status !== 'done').length;
  const done = allTasks.filter(t => t.status === 'done').length;
  const overdue = allTasks.filter(t => t.is_overdue).length;
  const docs = allDocs.length;

  const s = els.stats();
  s.innerHTML = `
    <div class="stat"><div class="k">Open tasks</div><div class="v">${open}</div></div>
    <div class="stat"><div class="k">Completed</div><div class="v">${done}</div></div>
    <div class="stat ${overdue > 0 ? 'stat-warning' : ''}"><div class="k">Overdue</div><div class="v">${overdue}</div></div>
    <div class="stat"><div class="k">Documents</div><div class="v">${docs}</div></div>
  `;

  const n = els.nextStep();
  if (!n) return;
  if (overdue > 0) n.textContent = `⚠️ You have ${overdue} overdue task(s). Complete them to stay inspection‑ready.`;
  else if (open > 0) n.textContent = 'Finish your next open task (keeps you inspection‑ready).';
  else if (docs === 0) n.textContent = 'Upload at least one supporting document (license, inspection, photo).';
  else n.textContent = 'Open the report and print/save it as your inspection binder.';
}

function setupDropzone() {
  const dz = els.dropzone();
  if (!dz) return;
  const fileInput = document.getElementById('docFile');

  dz.addEventListener('dragover', (e) => {
    e.preventDefault();
    dz.classList.add('drag');
  });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('drag');
    if (!e.dataTransfer?.files?.length) return;
    fileInput.files = e.dataTransfer.files;
    toast('File ready to upload');
  });
}

document.getElementById('loginBtn').onclick = login;
document.getElementById('registerBtn').onclick = register;
document.getElementById('createBinderBtn').onclick = createBinder;
document.getElementById('addTaskBtn').onclick = addTask;
document.getElementById('uploadDocBtn').onclick = uploadDoc;
document.getElementById('logoutBtn').onclick = logout;

// Sidebar search
els.binderSearch()?.addEventListener('input', renderBinders);

// Tabs
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => setTab(btn.dataset.tab));
});

// Task filters
document.querySelectorAll('.segBtn').forEach(btn => {
  btn.addEventListener('click', () => {
    taskFilter = btn.dataset.filter;
    document.querySelectorAll('.segBtn').forEach(b => b.classList.toggle('active', b === btn));
    renderTasks();
  });
});

// Report actions
document.getElementById('openReportBtn')?.addEventListener('click', openReport);
document.getElementById('copyReportBtn')?.addEventListener('click', copyReportHtml);

setupDropzone();

// Auto-login if token stored
if (token) {
  showApp();
  refreshBinders().catch(() => logout());
}
