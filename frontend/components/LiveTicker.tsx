'use client'

import { useState, useEffect } from 'react'

interface PriceTick {
    symbol: string
    price: number
    timestamp: string
    volume: number
}

export function LiveTicker() {
    const [prices, setPrices] = useState<PriceTick[]>([])
    const [lastUpdate, setLastUpdate] = useState<string>('')

    useEffect(() => {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
        const ws = new WebSocket(`${wsUrl}/stream`)

        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'subscribe',
                channels: ['prices']
            }))
        }

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data)

            if (message.type === 'price_update') {
                setPrices(message.data)
                setLastUpdate(new Date().toLocaleTimeString())
            }
        }

        return () => ws.close()
    }, [])

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">Live Prices</h3>
                <span className="text-xs text-gray-500">
                    Last update: {lastUpdate}
                </span>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
                {prices.map((tick, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <div className="flex-1">
                            <span className="font-medium text-gray-900">{tick.symbol}</span>
                            <span className="ml-2 text-sm text-gray-600">
                                Vol: {tick.volume.toLocaleString()}
                            </span>
                        </div>
                        <div className="text-right">
                            <div className="font-semibold text-gray-900">
                                ${tick.price.toFixed(2)}
                            </div>
                            <div className="text-xs text-gray-500">
                                {new Date(tick.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}