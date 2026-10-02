const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8002';

export async function api(path, options = {}) {
  const token = path.startsWith('/admin') ? localStorage.getItem('admin_token') : localStorage.getItem('token');
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join(', ') : data.detail;
    throw new Error(detail || 'Request failed');
  }
  return data;
}

export { API_BASE };
