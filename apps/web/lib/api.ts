import axios from 'axios'

/**
 * Maily API client for making requests to the backend
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Add request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('maily-auth-token') : null

    // Add token to headers if it exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized errors - refresh token or redirect to login
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem('maily-refresh-token')

        if (refreshToken) {
          const response = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'}/api/auth/refresh`,
            { refreshToken }
          )

          if (response.data.success) {
            // Update stored tokens
            localStorage.setItem('maily-auth-token', response.data.token)
            localStorage.setItem('maily-refresh-token', response.data.refreshToken)

            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${response.data.token}`
            return apiClient(originalRequest)
          }
        }

        // If refresh failed or no refresh token, redirect to login
        if (typeof window !== 'undefined') {
          // Clear tokens
          localStorage.removeItem('maily-auth-token')
          localStorage.removeItem('maily-refresh-token')

          // Redirect to login page
          window.location.href = '/auth/login'
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)

        // Redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('maily-auth-token')
          localStorage.removeItem('maily-refresh-token')
          window.location.href = '/auth/login'
        }
      }
    }

    // Standardize error structure
    const errorResponse = {
      status: error.response?.status || 500,
      statusText: error.response?.statusText || 'Unknown Error',
      data: error.response?.data || { message: error.message },
      headers: error.response?.headers || {}
    }

    return Promise.reject(errorResponse)
  }
)

/**
 * Helper methods for common API operations
 */
export const apiHelpers = {
  /**
   * Fetch content for the email canvas
   */
  fetchCanvasContent: async (campaignId: string) => {
    try {
      const response = await apiClient.get(`/api/campaigns/${campaignId}/canvas`)
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch canvas content:', error)
      throw error
    }
  },

  /**
   * Save canvas content
   */
  saveCanvasContent: async (campaignId: string, content: any) => {
    try {
      const response = await apiClient.put(`/api/campaigns/${campaignId}/canvas`, { content })
      return response.data
    } catch (error) {
      console.error('Failed to save canvas content:', error)
      throw error
    }
  },

  /**
   * Request AI suggestions for the canvas
   */
  getContentSuggestions: async (params: {
    campaignId: string,
    canvasState: any,
    contentText?: string
  }) => {
    try {
      const response = await apiClient.post('/api/ai/canvas/content-suggestions', params)
      return response.data.suggestions || []
    } catch (error) {
      console.error('Failed to get content suggestions:', error)
      return []
    }
  },

  /**
   * Request design suggestions for the canvas
   */
  getDesignSuggestions: async (params: {
    campaignId: string,
    canvasState: any
  }) => {
    try {
      const response = await apiClient.post('/api/ai/canvas/design-suggestions', params)
      return response.data.suggestions || []
    } catch (error) {
      console.error('Failed to get design suggestions:', error)
      return []
    }
  },

  /**
   * Export the canvas to HTML for email sending
   */
  exportCanvasToHtml: async (campaignId: string) => {
    try {
      const response = await apiClient.post(`/api/campaigns/${campaignId}/export`)
      return response.data.data
    } catch (error) {
      console.error('Failed to export canvas to HTML:', error)
      throw error
    }
  }
}
