import { TrendingUp, TrendingDown } from 'lucide-react'

interface KpiCardProps {
    title: string
    value: number
    format?: 'currency' | 'percentage' | 'number'
    trend?: 'up' | 'down'
    color?: 'primary' | 'success' | 'danger'
    subtitle?: string
}

export function KpiCard({
    title,
    value,
    format = 'number',
    trend,
    color = 'primary',
    subtitle
}: KpiCardProps) {
    const formatValue = (val: number) => {
        switch (format) {
            case 'currency':
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                }).format(val)
            case 'percentage':
                return `${val.toFixed(2)}%`
            default:
                return val.toLocaleString()
        }
    }

    const colorClasses = {
        primary: 'text-primary-600',
        success: 'text-green-600',
        danger: 'text-red-600'
    }

    const trendIcon = trend === 'up' ? (
        <TrendingUp className="w-5 h-5 text-green-500" />
    ) : trend === 'down' ? (
        <TrendingDown className="w-5 h-5 text-red-500" />
    ) : null

    return (
        <div className="kpi-card">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">{title}</p>
                    <p className={`text-2xl font-semibold ${colorClasses[color]}`}>
                        {formatValue(value)}
                    </p>
                    {subtitle && (
                        <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
                    )}
                </div>
                {trendIcon && (
                    <div className="ml-4">
                        {trendIcon}
                    </div>
                )}
            </div>
        </div>
    )
}