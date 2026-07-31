import { useAuthStore } from '../store/authStore'
import { useNavigationStore } from '../store/navigationStore'

const BASE_URL = '/api/v1'

interface RequestOptions extends RequestInit {
  json?: any
}

export async function apiRequest(path: string, options: RequestOptions = {}) {
  const { token, refreshToken, login, logout } = useAuthStore.getState()
  const { navigateTo } = useNavigationStore.getState()
  
  const headers = new Headers(options.headers || {})
  
  // JSON helper
  if (options.json && !options.body) {
    headers.set('Content-Type', 'application/json')
    options.body = JSON.stringify(options.json)
  }
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  const finalOptions = {
    ...options,
    headers
  }
  
  let response = await fetch(`${BASE_URL}${path}`, finalOptions)
  
  // Check if token expired and refresh is available
  if (response.status === 401 && refreshToken) {
    try {
      const refreshResp = await fetch(`${BASE_URL}/auth/refresh?refresh_token=${refreshToken}`, {
        method: 'POST'
      })
      
      if (refreshResp.ok) {
        const refreshData = await refreshResp.json()
        
        // Fetch current user details to update store
        const userResp = await fetch(`${BASE_URL}/auth/me`, {
          headers: { 'Authorization': `Bearer ${refreshData.access_token}` }
        })
        
        if (userResp.ok) {
          const userData = await userResp.json()
          // Update store
          login(refreshData.access_token, refreshData.refresh_token, userData)
          
          // Retry original request with new token
          headers.set('Authorization', `Bearer ${refreshData.access_token}`)
          response = await fetch(`${BASE_URL}${path}`, {
            ...options,
            headers
          })
        }
      } else {
        // Refresh failed -> logout
        logout()
        navigateTo('login')
      }
    } catch (err) {
      console.error("Token refresh failed", err)
      logout()
      navigateTo('login')
    }
  }
  
  return response
}
