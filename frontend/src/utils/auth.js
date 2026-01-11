export const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '/api')

export const getToken = () => null
export const setToken = (token) => { }
export const removeToken = () => { }

export const apiRequest = async (endpoint, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || 'An error occurred')
  }

  return response.json()
}

export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || 'An error occurred')
  }

  return response.json()
}
