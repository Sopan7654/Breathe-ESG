import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5037',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inject company and analyst identity on every request
api.interceptors.request.use((config) => {
  config.headers['X-Company-Id'] = import.meta.env.VITE_COMPANY_ID || '11111111-1111-1111-1111-111111111111';
  config.headers['X-Analyst-Name'] = import.meta.env.VITE_ANALYST_NAME || 'Analyst';
  return config;
});

export default api;
