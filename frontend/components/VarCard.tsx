'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'
import { api } from '../lib/api'

interface VarData {
    var_value: number
    confidence_level: number
    lookback_days: number
    method: string
    portfolio_value: number
}

export function VarCard() {
    const [varData, setVarData] = useState<VarData | null>(null)
    const [loading, setLoading] = useState(true)
    const [method, setMethod] = useState<'historical' | 'parametric' | 'ewma'>('historical')
    const [alpha, setAlpha] = useState(0.99)

    useEffect(() => {
        loadVarData()
    }, [method, alpha])

    const loadVarData = async () => {
        try {
            setLoading(true)
            const response = await api.get('/risk/var', {
                params: {
                    method,
                    alpha,
                    lookback: 250
                }
            })
            setVarData(response.data)
        } catch (error) {
            console.error('Failed to load VaR data:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value)
    }

    const getVarRiskLevel = (varValue: number, portfolioValue: number) => {
        const varPercent = (varValue / portfolioValue) * 100
        if (varPercent > 10) return { level: 'high', color: 'red' }
        if (varPercent > 5) return { level: 'medium', color: 'yellow' }
        return { level: 'low', color: 'green' }
    }

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
            </div>
        )
    }

    if (!varData) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center text-gray-500">
                    <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
                    <p>Unable to load VaR data</p>
                </div>
            </div>
        )
    }

    const risk = getVarRiskLevel(varData.var_value, varData.portfolio_value)
    const varPercent = (varData.var_value / varData.portfolio_value) * 100

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Value at Risk</h3>
                <div className="flex space-x-2">
                    {(['historical', 'parametric', 'ewma'] as const).map((m) => (
                        <button
                            key={m}
                            onClick={() => setMethod(m)}
                            className={`px-2 py-1 text-xs rounded capitalize ${method === m
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            {m}
                        </button>
                    ))}
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <div className="flex items-center space-x-2 mb-1">
                        <span className="text-2xl font-bold text-gray-900">
                            {formatCurrency(varData.var_value)}
                        </span>
                        <div className={`w-3 h-3 rounded-full bg-${risk.color}-500`}></div>
                    </div>
                    <p className="text-sm text-gray-600">
                        {(varData.confidence_level * 100).toFixed(0)}% confidence, {varData.lookback_days} days
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-gray-500">% of Portfolio</p>
                        <p className="font-semibold">{varPercent.toFixed(2)}%</p>
                    </div>
                    <div>
                        <p className="text-gray-500">Risk Level</p>
                        <p className={`font-semibold capitalize text-${risk.color}-600`}>
                            {risk.level}
                        </p>
                    </div>
                </div>

                <div className="border-t pt-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700">
                            Confidence Level:
                        </label>
                        <select
                            value={alpha}
                            onChange={(e) => setAlpha(parseFloat(e.target.value))}
                            className="text-sm border border-gray-300 rounded px-2 py-1"
                        >
                            <option value={0.95}>95%</option>
                            <option value={0.99}>99%</option>
                            <option value={0.999}>99.9%</option>
                        </select>
                    </div>
                    <p className="text-xs text-gray-500">
                        Method: {method.charAt(0).toUpperCase() + method.slice(1)}
                    </p>
                </div>
            </div>
        </div>
    )
}