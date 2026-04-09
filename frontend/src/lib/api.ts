import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
})

// In dev mode, set the static token immediately at module load time so it is
// present before any React component mounts or React Query fires its first request.
// Never use useEffect for this — effects run after render, creating a race condition.
if (import.meta.env.VITE_DEV_MODE === 'true' && import.meta.env.VITE_DEV_TOKEN) {
  api.defaults.headers.common['Authorization'] = `Bearer ${import.meta.env.VITE_DEV_TOKEN}`
}

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}
