'use client'

import { useState, useEffect } from 'react'
import { ChevronUp, ChevronDown, Search, Filter } from 'lucide-react'
import { api } from '../lib/api'

interface Position {
    id: number
    symbol: string
    quantity: number
    average_cost: number
    market_value: number
    unrealized_pnl: number
}

type SortField = 'symbol' | 'quantity' | 'market_value' | 'unrealized_pnl'
type SortOrder = 'asc' | 'desc'

export function PositionsTable() {
    const [positions, setPositions] = useState<Position[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [sortField, setSortField] = useState<SortField>('unrealized_pnl')
    const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

    useEffect(() => {
        loadPositions()
    }, [])

    const loadPositions = async () => {
        try {
            const response = await api.get('/positions')
            setPositions(response.data)
        } catch (error) {
            console.error('Failed to load positions:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
        } else {
            setSortField(field)
            setSortOrder('desc')
        }
    }

    const filteredAndSortedPositions = positions
        .filter(position =>
            position.symbol.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .sort((a, b) => {
            const aVal = a[sortField]
            const bVal = b[sortField]
            const multiplier = sortOrder === 'asc' ? 1 : -1

            if (typeof aVal === 'string') {
                return aVal.localeCompare(bVal as string) * multiplier
            }
            return (Number(aVal) - Number(bVal)) * multiplier
        })

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(value)
    }

    const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) return null
        return sortOrder === 'asc' ?
            <ChevronUp className="w-4 h-4" /> :
            <ChevronDown className="w-4 h-4" />
    }

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-12 bg-gray-100 rounded"></div>
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="bg-white rounded-lg shadow">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Positions</h2>
                    <div className="text-sm text-gray-500">
                        {filteredAndSortedPositions.length} positions
                    </div>
                </div>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="Search symbols..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full sm:w-64"
                    />
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th
                                onClick={() => handleSort('symbol')}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                                <div className="flex items-center space-x-1">
                                    <span>Symbol</span>
                                    <SortIcon field="symbol" />
                                </div>
                            </th>
                            <th
                                onClick={() => handleSort('quantity')}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                                <div className="flex items-center space-x-1">
                                    <span>Quantity</span>
                                    <SortIcon field="quantity" />
                                </div>
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Avg Cost
                            </th>
                            <th
                                onClick={() => handleSort('market_value')}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                                <div className="flex items-center space-x-1">
                                    <span>Market Value</span>
                                    <SortIcon field="market_value" />
                                </div>
                            </th>
                            <th
                                onClick={() => handleSort('unrealized_pnl')}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                                <div className="flex items-center space-x-1">
                                    <span>Unrealized P&L</span>
                                    <SortIcon field="unrealized_pnl" />
                                </div>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {filteredAndSortedPositions.map((position) => (
                            <tr key={position.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-medium text-gray-900">
                                        {position.symbol}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {position.quantity.toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {formatCurrency(position.average_cost)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {formatCurrency(position.market_value)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <span
                                        className={
                                            position.unrealized_pnl >= 0
                                                ? 'text-green-600'
                                                : 'text-red-600'
                                        }
                                    >
                                        {formatCurrency(position.unrealized_pnl)}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {filteredAndSortedPositions.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    No positions found matching your search.
                </div>
            )}
        </div>
    )
}