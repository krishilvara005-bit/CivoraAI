export class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

async function request(path, { method = 'GET', body, form } = {}) {
  const opts = { method, headers: {} };
  if (form) opts.body = form;
  else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(`/api${path}`, opts);
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0);
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(data?.error || `Request failed (${res.status}).`, res.status, data?.fields);
  return data;
}

export const api = {
  listProjects: () => request('/projects').then((d) => d.projects),
  createProject: (name) => request('/projects', { method: 'POST', body: { name } }),
  getProject: (id) => request(`/projects/${id}`),
  deleteProject: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
  uploadPlan: (id, file) => {
    const form = new FormData();
    form.append('file', file);
    return request(`/projects/${id}/plan`, { method: 'POST', form });
  },
  planUrl: (id, version) => `/api/projects/${id}/plan/file?v=${encodeURIComponent(version || '')}`,
  rereadPlan: (id) => request(`/projects/${id}/plan/read`, { method: 'POST' }),
  getModel: (id) => request(`/projects/${id}/model`),
  saveInputs: (id, patch) => request(`/projects/${id}/inputs`, { method: 'PUT', body: patch }),
  ask: (messages, context = {}) => request('/assistant', { method: 'POST', body: { messages, ...context } }),
};

export const ALLOWED = '.jpg,.jpeg,.png,.pdf,.dxf,.dwg';
export const fmtSize = (b) => (b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);
