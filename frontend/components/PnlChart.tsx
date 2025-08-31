'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../lib/api'

interface PnlData {
    date: string
    total_pnl: number
    unrealized_pnl: number
    realized_pnl: number
}

export function PnlChart() {
    const [data, setData] = useState<PnlData[]>([])
    const [loading, setLoading] = useState(true)
    const [timeframe, setTimeframe] = useState('30d')

    useEffect(() => {
        loadPnlData()
    }, [timeframe])

    const loadPnlData = async () => {
        try {
            const response = await api.get('/pnl/timeseries', {
                params: {
                    days: timeframe === '30d' ? 30 : timeframe === '7d' ? 7 : 90
                }
            })
            setData(response.data)
        } catch (error) {
            console.error('Failed to load P&L data:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        })
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Timeframe selector */}
            <div className="flex space-x-2">
                {['7d', '30d', '90d'].map((tf) => (
                    <button
                        key={tf}
                        onClick={() => setTimeframe(tf)}
                        className={`px-3 py-1 text-sm rounded ${timeframe === tf
                            ? 'bg-primary-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {tf}
                    </button>
                ))}
            </div>

            {/* Chart */}
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={formatDate}
                            tick={{ fontSize: 12 }}
                        />
                        <YAxis
                            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                            tick={{ fontSize: 12 }}
                        />
                        <Tooltip
                            formatter={(value: number) => [`$${value.toLocaleString()}`, 'P&L']}
                            labelFormatter={(date) => formatDate(date)}
                        />
                        <Line
                            type="monotone"
                            dataKey="total_pnl"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={false}
                        />
                        <Line
                            type="monotone"
                            dataKey="unrealized_pnl"
                            stroke="#10b981"
                            strokeWidth={1}
                            strokeDasharray="5 5"
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}