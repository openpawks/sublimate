const API = {
  projects: '/api/v0/projects',
  tasks: '/api/v0/tasks',
  providers: '/api/v0/providers',
};

const container = document.getElementById('view-container');

// ─── Helpers ──────────────────────────────────────

function esc(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('en-CA');
}

function showFlash(msg, type) {
  const el = document.createElement('div');
  el.className = `flash flash-${type || 'error'}`;
  el.textContent = msg;
  container.prepend(el);
  setTimeout(() => { el.remove(); }, 5000);
}

function openBadge(open) {
  if (open === false) {
    return '<span class="badge badge-closed">closed</span>';
  }
  return '<span class="badge badge-open">open</span>';
}

// ─── API ──────────────────────────────────────────

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const info = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(info.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiPost(path, data) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const info = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(info.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(path, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) {
    const info = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(info.detail || `Request failed (${res.status})`);
  }
}

// ─── View: Projects List ─────────────────────────

async function renderProjects() {
  container.innerHTML = '<div class="view-header"><h2>Projects</h2><p>All projects</p></div><div class="empty-state">Loading\u2026</div>';
  try {
    const projects = await apiGet(API.projects);
    if (!projects.length) {
      container.innerHTML = '<div class="view-header"><h2>Projects</h2><p>All projects</p></div><div class="empty-state">No projects yet.</div>';
      return;
    }
    let html = `<div class="view-header"><h2>Projects</h2><p>${
      projects.length
    } project${
      projects.length !== 1 ? 's' : ''
    }</p></div>`
      + '<table class="data-table"><thead><tr><th>ID</th><th>Name</th><th>Root Dir</th><th>Created</th></tr></thead><tbody>';
    projects.forEach((p) => {
      html += `<tr data-go="project-detail?projectId=${
        p.id
      }" class="clickable"><td>${
        p.id
      }</td><td><strong>${
        esc(p.name)
      }</strong></td><td class="meta">${
        esc(p.root_dir)
      }</td><td class="meta">${
        formatDate(p.created_at)
      }</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Projects</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Project Detail ────────────────────────

async function renderProjectDetail(projectId) {
  container.innerHTML = '<div class="view-header"><h2>Project</h2><p class="meta">Loading\u2026</p></div>';
  try {
    const project = await apiGet(`${API.projects}/${projectId}`);
    const tasks = await apiGet(`${API.tasks}?project_id=${projectId}`);

    let html = '<div class="view-header">'
      + '<a href="#" data-go="projects" class="back-link">&larr; Projects</a>'
      + `<h2>${esc(project.name)}</h2>`
      + `<p class="meta">ID ${project.id
      } &middot; ${esc(project.root_dir)
      } &middot; Created ${formatDate(project.created_at)
      }</p></div>`
      + '<div class="section-actions">'
      + `<button data-go="create-task?projectId=${project.id
      }" class="btn btn-primary">+ New Task for this Project</button>`
      + ' <button id="btn-delete-project" class="btn btn-danger">Delete Project</button>'
      + '</div>';

    if (!tasks.length) {
      html += '<div class="empty-state">No tasks for this project yet.</div>';
    } else {
      html += '<table class="data-table"><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Created</th></tr></thead><tbody>';
      tasks.forEach((t) => {
        html += `<tr data-go="task-detail?taskId=${
          t.id
        }" class="clickable"><td>${t.id
        }</td><td><strong>${esc(t.name)
        }</strong></td><td>${openBadge(t.open)
        }</td><td class="meta">${formatDate(t.created_at)
        }</td></tr>`;
      });
      html += '</tbody></table>';
    }

    container.innerHTML = html;

    document.getElementById('btn-delete-project').addEventListener('click', async () => {
      if (!window.confirm(`Delete project "${project.name}" and all its tasks?`)) return;
      try {
        await apiDelete(`${API.projects}/${projectId}`);
        showFlash('Project deleted.', 'success');
        renderProjects();
      } catch (err) {
        showFlash(err.message);
      }
    });
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Project</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Tasks List ────────────────────────────

async function renderTasks() {
  container.innerHTML = '<div class="view-header"><h2>Tasks</h2><p>All tasks</p></div><div class="empty-state">Loading\u2026</div>';
  try {
    const tasks = await apiGet(API.tasks);
    if (!tasks.length) {
      container.innerHTML = '<div class="view-header"><h2>Tasks</h2><p>All tasks</p></div><div class="empty-state">No tasks yet.</div>';
      return;
    }
    let html = `<div class="view-header"><h2>Tasks</h2><p>${
      tasks.length
    } task${
      tasks.length !== 1 ? 's' : ''
    }</p></div>`
      + '<table class="data-table"><thead><tr><th>ID</th><th>Name</th><th>Project</th><th>Status</th><th>Created</th></tr></thead><tbody>';
    tasks.forEach((t) => {
      html += `<tr data-go="task-detail?taskId=${
        t.id
      }" class="clickable"><td>${t.id
      }</td><td><strong>${esc(t.name)
      }</strong></td><td>${t.project_id
      }</td><td>${openBadge(t.open)
      }</td><td class="meta">${formatDate(t.created_at)
      }</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Tasks</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Task Detail ───────────────────────────

async function renderTaskDetail(taskId) {
  container.innerHTML = '<div class="view-header"><h2>Task</h2><p class="meta">Loading\u2026</p></div>';
  try {
    const task = await apiGet(`${API.tasks}/${taskId}`);

    const html = '<div class="view-header">'
      + '<a href="#" data-go="tasks" class="back-link">&larr; Tasks</a>'
      + `<h2>${esc(task.name)}</h2>`
      + `<p class="meta">Created ${formatDate(task.created_at)}</p>`
      + '</div>'
      + '<table class="detail-table">'
      + `<tr><th>ID</th><td>${task.id}</td></tr>`
      + `<tr><th>Name</th><td><strong>${esc(task.name)}</strong></td></tr>`
      + `<tr><th>Project</th><td>${task.project_id}</td></tr>`
      + `<tr><th>Root Dir</th><td class="meta">${esc(task.root_dir)}</td></tr>`
      + `<tr><th>Status</th><td>${openBadge(task.open)}</td></tr>`
      + `<tr><th>Todos</th><td>${esc(task.todos || '-')}</td></tr>`
      + `<tr><th>Settings YAML</th><td class="meta">${esc(task.settings_yaml || '-')}</td></tr>`
      + `<tr><th>Created</th><td class="meta">${formatDate(task.created_at)}</td></tr>`
      + '</table>';

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Task</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Project / Tasks (filtered) ────────────

async function renderProjectTasks() {
  container.innerHTML = '<div class="view-header"><h2>Project / Tasks</h2><p>View tasks filtered by project</p></div><div class="empty-state">Loading\u2026</div>';
  try {
    const projects = await apiGet(API.projects);
    let html = '<div class="view-header"><h2>Project / Tasks</h2><p>View tasks filtered by project</p></div>'
      + '<div class="filter-bar"><label for="pt-project">Project</label>'
      + '<select id="pt-project"><option value="">\u2014 Select a project \u2014</option>';
    projects.forEach((p) => {
      html += `<option value="${p.id}">${esc(p.name)}</option>`;
    });
    html += '</select></div><div id="pt-results"><div class="empty-state">Select a project to view its tasks.</div></div>';
    container.innerHTML = html;

    document.getElementById('pt-project').addEventListener('change', function () {
      const pid = this.value;
      const results = document.getElementById('pt-results');
      if (!pid) {
        results.innerHTML = '<div class="empty-state">Select a project to view its tasks.</div>';
        return;
      }
      results.innerHTML = '<div class="empty-state">Loading\u2026</div>';
      apiGet(`${API.tasks}?project_id=${pid}`)
        .then((tasks) => {
          if (!tasks.length) {
            results.innerHTML = '<div class="empty-state">No tasks for this project.</div>';
            return;
          }
          let tbl = '<table class="data-table"><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Created</th></tr></thead><tbody>';
          tasks.forEach((t) => {
            tbl += `<tr><td>${t.id
            }</td><td><strong>${esc(t.name)
            }</strong></td><td>${openBadge(t.open)
            }</td><td class="meta">${formatDate(t.created_at)
            }</td></tr>`;
          });
          tbl += '</tbody></table>';
          results.innerHTML = tbl;
        })
        .catch((err) => {
          results.innerHTML = `<div class="flash flash-error">${esc(err.message)}</div>`;
        });
    });
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Project / Tasks</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Providers List ────────────────────────

async function renderProviders() {
  container.innerHTML = '<div class="view-header"><h2>Providers</h2><p>All connected providers</p></div><div class="empty-state">Loading\u2026</div>';
  try {
    const providers = await apiGet(API.providers);
    if (!providers.length) {
      container.innerHTML = '<div class="view-header"><h2>Providers</h2><p>All connected providers</p></div><div class="empty-state">No providers connected.</div>';
      return;
    }
    let html = `<div class="view-header"><h2>Providers</h2><p>${
      providers.length} provider${
      providers.length !== 1 ? 's' : ''
    }</p></div>`
      + '<table class="data-table"><thead><tr><th>Nickname</th><th>Provider</th><th>API Key</th><th>Created</th><th></th></tr></thead><tbody>';
    providers.forEach((p) => {
      html += `<tr><td><strong>${esc(p.id)
      }</strong></td><td>${esc(p.name)
      }</td><td class="meta">${esc(p.api_key)
      }</td><td class="meta">${formatDate(p.created_at)
      }</td><td><button class="btn btn-danger btn-sm" data-delete-provider="${p.id}">Delete</button></td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;

    container.querySelectorAll('[data-delete-provider]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.deleteProvider;
        if (!window.confirm(`Delete provider "${id}"?`)) return;
        try {
          await apiDelete(`${API.providers}/${encodeURIComponent(id)}`);
          showFlash('Provider deleted.', 'success');
          renderProviders();
        } catch (err) {
          showFlash(err.message);
        }
      });
    });
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>Providers</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Create Project ────────────────────────

function renderCreateProject() {
  container.innerHTML = '<div class="view-header"><h2>New Project</h2></div>'
    + '<form id="form-create-project">'
    + '<div class="form-group"><label for="fp-name">Name</label><input type="text" id="fp-name" name="name" required placeholder="my-project"></div>'
    + '<div class="form-group"><label for="fp-root">Root Directory</label><input type="text" id="fp-root" name="root_dir" required placeholder="/path/to/project"></div>'
    + '<div class="form-group"><label for="fp-settings">Settings YAML <span class="meta">(optional)</span></label><textarea id="fp-settings" name="settings_yaml" placeholder="key: value"></textarea></div>'
    + '<div class="form-actions"><button type="submit" class="btn btn-primary">Create Project</button></div>'
    + '</form>';

  document.getElementById('form-create-project').addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = e.currentTarget;
    try {
      await apiPost(API.projects, {
        name: f.name.value.trim(),
        root_dir: f.root_dir.value.trim(),
        user_id: 0,
        settings_yaml: f.settings_yaml.value.trim() || null,
      });
      showFlash('Project created.', 'success');
      f.reset();
    } catch (err) {
      showFlash(err.message);
    }
  });
}

// ─── View: Create Task ───────────────────────────

async function renderCreateTask(preSelectedProjectId) {
  container.innerHTML = '<div class="view-header"><h2>New Task</h2></div><div class="empty-state">Loading\u2026</div>';
  try {
    const projects = await apiGet(API.projects);
    let html = '<div class="view-header"><h2>New Task</h2></div>'
      + '<form id="form-create-task">'
      + '<div class="form-group"><label for="ft-project">Project</label>'
      + '<select id="ft-project" name="project_id" required>';
    if (!projects.length) {
      html += '<option value="">No projects available</option>';
    } else {
      html += '<option value="">\u2014 Select \u2014</option>';
      projects.forEach((p) => {
        html += `<option value="${p.id}"${
          String(p.id) === String(preSelectedProjectId) ? ' selected' : ''
        }>${esc(p.name)}</option>`;
      });
    }
    html += '</select></div>'
      + '<div class="form-group"><label for="ft-name">Name</label><input type="text" id="ft-name" name="name" required placeholder="my-task"></div>'
      + '<div class="form-group"><label for="ft-root">Root Directory</label><input type="text" id="ft-root" name="root_dir" required placeholder="/path/to/worktree"></div>'
      + '<div class="form-group"><label for="ft-todos">Todos <span class="meta">(optional)</span></label><textarea id="ft-todos" name="todos" placeholder="Short todo list for the AI"></textarea></div>'
      + '<div class="form-group"><label for="ft-settings">Settings YAML <span class="meta">(optional)</span></label><textarea id="ft-settings" name="settings_yaml" placeholder="key: value"></textarea></div>'
      + `<div class="form-actions"><button type="submit" class="btn btn-primary"${
        projects.length ? '' : ' disabled'
      }>Create Task</button></div>`
      + '</form>';
    container.innerHTML = html;

    if (!projects.length) return;

    document.getElementById('form-create-task').addEventListener('submit', async (e) => {
      e.preventDefault();
      const f = e.currentTarget;
      const projectId = parseInt(f.project_id.value, 10);
      if (!projectId) {
        showFlash('Please select a project.');
        return;
      }
      try {
        await apiPost(API.tasks, {
          name: f.name.value.trim(),
          project_id: projectId,
          root_dir: f.root_dir.value.trim(),
          todos: f.todos.value.trim() || null,
          settings_yaml: f.settings_yaml.value.trim() || null,
        });
        showFlash('Task created.', 'success');
        f.reset();
      } catch (err) {
        showFlash(err.message);
      }
    });
  } catch (err) {
    container.innerHTML = '<div class="view-header"><h2>New Task</h2></div>';
    showFlash(err.message);
  }
}

// ─── View: Create Provider ───────────────────────

function renderCreateProvider() {
  container.innerHTML = '<div class="view-header"><h2>Connect Provider</h2></div>'
    + '<form id="form-create-provider">'
    + '<div class="form-group"><label for="fpv-id">Nickname</label><input type="text" id="fpv-id" name="id" required placeholder="my-provider"></div>'
    + '<div class="form-group"><label for="fpv-name">Provider</label><input type="text" id="fpv-name" name="name" required placeholder="openai, deepseek, ollama, ..."></div>'
    + '<div class="form-group"><label for="fpv-key">API Key</label><input type="text" id="fpv-key" name="api_key" required placeholder="sk-..."></div>'
    + '<div class="form-actions"><button type="submit" class="btn btn-primary">Connect Provider</button></div>'
    + '</form>';

  document.getElementById('form-create-provider').addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = e.currentTarget;
    try {
      await apiPost(API.providers, {
        id: f.id.value.trim(),
        name: f.name.value.trim(),
        api_key: f.api_key.value.trim(),
      });
      showFlash('Provider connected.', 'success');
      f.reset();
    } catch (err) {
      showFlash(err.message);
    }
  });
}

// ─── View Router ─────────────────────────────────

function renderView(view, params) {
  switch (view) {
    case 'projects':
      renderProjects();
      break;
    case 'project-detail':
      renderProjectDetail(params.projectId);
      break;
    case 'tasks':
      renderTasks();
      break;
    case 'task-detail':
      renderTaskDetail(params.taskId);
      break;
    case 'project-tasks':
      renderProjectTasks();
      break;
    case 'providers':
      renderProviders();
      break;
    case 'create-project':
      renderCreateProject();
      break;
    case 'create-task':
      renderCreateTask(params.projectId);
      break;
    case 'create-provider':
      renderCreateProvider();
      break;
    default:
      renderProjects();
      break;
  }
}

// ─── Navigation ──────────────────────────────────

function getNavKey(view) {
  const map = {
    projects: 'projects',
    'project-detail': 'projects',
    tasks: 'tasks',
    'task-detail': 'tasks',
  };
  return map[view] || view;
}

function navigate(view, params) {
  const p = params || {};
  const key = getNavKey(view);
  document.querySelectorAll('.nav-link').forEach((l) => {
    l.classList.toggle('active', l.dataset.view === key);
  });
  renderView(view, p);
}

// ─── Event: Nav clicks ──────────────────────────

document.querySelector('.nav-list').addEventListener('click', (e) => {
  const link = e.target.closest('.nav-link');
  if (!link) return;
  e.preventDefault();
  navigate(link.dataset.view);
});

// ─── Event: Content clicks (delegated) ──────────

container.addEventListener('click', (e) => {
  const trigger = e.target.closest('[data-go]');
  if (!trigger) return;
  e.preventDefault();
  const raw = trigger.dataset.go;
  const parts = raw.split('?');
  const view = parts[0];
  const params = {};
  if (parts[1]) {
    parts[1].split('&').forEach((pair) => {
      const kv = pair.split('=');
      const k = kv[0];
      const v = kv[1];
      params[k] = v;
    });
  }
  navigate(view, params);
});

// ─── Boot ────────────────────────────────────────

navigate('projects');
