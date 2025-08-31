const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Demo token for development
const DEMO_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJhY2NvdW50X2lkIjoiZGVtbyIsImV4cCI6MTc1NjY3NjgwMH0.demo-token'

class ApiClient {
    private baseURL: string
    private token: string | null = null

    constructor(baseURL: string) {
        this.baseURL = baseURL
        this.token = DEMO_TOKEN // For development
    }

    private getHeaders(): HeadersInit {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        }

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`
        }

        return headers
    }

    async get(endpoint: string, options?: { params?: Record<string, any> }) {
        let url = `${this.baseURL}/api${endpoint}`

        if (options?.params) {
            const searchParams = new URLSearchParams()
            Object.entries(options.params).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    searchParams.append(key, value.toString())
                }
            })
            url += `?${searchParams.toString()}`
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: this.getHeaders(),
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return { data: await response.json() }
    }

    async post(endpoint: string, data?: any) {
        const response = await fetch(`${this.baseURL}/api${endpoint}`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: data ? JSON.stringify(data) : undefined,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return { data: await response.json() }
    }

    async put(endpoint: string, data?: any) {
        const response = await fetch(`${this.baseURL}/api${endpoint}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: data ? JSON.stringify(data) : undefined,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return { data: await response.json() }
    }

    async delete(endpoint: string) {
        const response = await fetch(`${this.baseURL}/api${endpoint}`, {
            method: 'DELETE',
            headers: this.getHeaders(),
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return { data: await response.json() }
    }

    setToken(token: string) {
        this.token = token
    }
}

export const api = new ApiClient(API_BASE_URL)