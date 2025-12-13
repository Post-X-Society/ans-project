import axios from 'axios';

// Get API URL from environment or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
	baseURL: API_URL,
	headers: {
		'Content-Type': 'application/json'
	},
	timeout: 10000 // 10 second timeout
});

// Request interceptor - can add auth tokens here later
apiClient.interceptors.request.use(
	(config) => {
		// Future: Add authentication token
		// const token = getAuthToken();
		// if (token) {
		//   config.headers.Authorization = `Bearer ${token}`;
		// }
		return config;
	},
	(error) => {
		return Promise.reject(error);
	}
);

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
	(response) => response,
	(error) => {
		// Handle different error scenarios
		if (error.response) {
			// Server responded with error status
			console.error('API Error:', error.response.status, error.response.data);
		} else if (error.request) {
			// Request made but no response
			console.error('Network Error:', error.message);
		} else {
			// Something else happened
			console.error('Error:', error.message);
		}
		return Promise.reject(error);
	}
);
