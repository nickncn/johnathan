import { PositionsTable } from '@/components/PositionsTable'

export default function PositionsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Portfolio Positions</h1>
                <p className="mt-2 text-gray-600">
                    Current positions with real-time P&L and market values
                </p>
            </div>

            <PositionsTable />
        </div>
    )
}