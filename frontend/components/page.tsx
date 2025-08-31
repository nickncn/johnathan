'use client'

import { useState, useEffect } from 'react'
import { KpiCard } from '../components/KpiCard'
import { LiveTicker } from '../components/LiveTicker'
import { PnlChart } from '../components/PnlChart'
import { api } from '../lib/api'

interface DashboardData {
    pnl: {
        total_pnl: number
        unrealized_pnl: number
        portfolio_value: number
    }
    var: {
        var_value: number
        confidence_level: number
    }
    positions: Array<{
        symbol: string
        unrealized_pnl: number
    }>
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardData | null>(null)
    const [loading, setLoading] = useState(true)
    const [wsConnected, setWsConnected] = useState(false)

    useEffect(() => {
        loadDashboardData()
        connectWebSocket()
    }, [])

    const loadDashboardData = async () => {
        try {
            const [pnlRes, varRes, positionsRes] = await Promise.all([
                api.get('/pnl/summary'),
                api.get('/risk/var'),
                api.get('/positions')
            ])

            setData({
                pnl: pnlRes.data,
                var: varRes.data,
                positions: positionsRes.data
            })
        } catch (error) {
            console.error('Failed to load dashboard data:', error)
        } finally {
            setLoading(false)
        }
    }

    const connectWebSocket = () => {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
        const ws = new WebSocket(`${wsUrl}/stream`)

        ws.onopen = () => {
            setWsConnected(true)
            // Subscribe to all channels
            ws.send(JSON.stringify({
                type: 'subscribe',
                channels: ['prices', 'pnl', 'alerts']
            }))
        }

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data)

            if (message.type === 'pnl_update') {
                setData(prev => prev ? { ...prev, pnl: message.data } : null)
            } else if (message.type === 'risk_alert') {
                // Show toast notification
                showAlert(message.data.message, message.data.severity)
            }
        }

        ws.onclose = () => {
            setWsConnected(false)
            // Reconnect after delay
            setTimeout(connectWebSocket, 5000)
        }
    }

    const showAlert = (message: string, severity: string) => {
        // Simple alert implementation
        const alertClass = severity === 'high' ? 'alert-danger' :
            severity === 'medium' ? 'alert-warning' : 'alert-success'

        const alertDiv = document.createElement('div')
        alertDiv.className = `fixed top-4 right-4 z-50 ${alertClass} max-w-md`
        alertDiv.textContent = message
        document.body.appendChild(alertDiv)

        setTimeout(() => {
            document.body.removeChild(alertDiv)
        }, 5000)
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header with connection status */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Portfolio Dashboard</h1>
                <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm text-gray-600">
                        {wsConnected ? 'Live' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <KpiCard
                    title="Total P&L"
                    value={data?.pnl.total_pnl || 0}
                    format="currency"
                    trend="up"
                />
                <KpiCard
                    title="Portfolio Value"
                    value={data?.pnl.portfolio_value || 0}
                    format="currency"
                />
                <KpiCard
                    title="99% VaR"
                    value={data?.var.var_value || 0}
                    format="currency"
                    trend="down"
                    color="danger"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold mb-4">P&L History</h2>
                    <PnlChart />
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold mb-4">Live Prices</h2>
                    <LiveTicker />
                </div>
            </div>

            {/* Top Positions */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Top Positions</h2>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Symbol
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Unrealized P&L
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {data?.positions?.slice(0, 5).map((position, index) => (
                                <tr key={index}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {position.symbol}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        <span className={position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                                            ${position.unrealized_pnl.toLocaleString()}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}