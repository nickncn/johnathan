'use client'

import { useState } from 'react'
import { Send, FileText, Calendar, User, Sparkles } from 'lucide-react'
import { api } from '../lib/api'

interface ReportRequest {
    alpha: number
    lookback_days: number
    save_report: boolean
}

interface GeneratedReport {
    summary: string
    account_id: string
    generated_at: string
    parameters: any
    report_id?: number
}

export function ReportPanel() {
    const [generating, setGenerating] = useState(false)
    const [report, setReport] = useState<GeneratedReport | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [params, setParams] = useState<ReportRequest>({
        alpha: 0.99,
        lookback_days: 250,
        save_report: true
    })

    const generateReport = async () => {
        try {
            setGenerating(true)
            setError(null)

            const response = await api.post('/llm/summary', params)
            setReport(response.data)
        } catch (err: any) {
            setError(err.message || 'Failed to generate report')
        } finally {
            setGenerating(false)
        }
    }

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    return (
        <div className="space-y-6">
            {/* Generation Controls */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center space-x-2 mb-4">
                    <Sparkles className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold text-gray-900">Generate AI Risk Report</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Confidence Level
                        </label>
                        <select
                            value={params.alpha}
                            onChange={(e) => setParams({ ...params, alpha: parseFloat(e.target.value) })}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                        >
                            <option value={0.95}>95%</option>
                            <option value={0.99}>99%</option>
                            <option value={0.999}>99.9%</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Lookback Days
                        </label>
                        <select
                            value={params.lookback_days}
                            onChange={(e) => setParams({ ...params, lookback_days: parseInt(e.target.value) })}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                        >
                            <option value={30}>30 days</option>
                            <option value={90}>90 days</option>
                            <option value={250}>250 days</option>
                            <option value={500}>500 days</option>
                        </select>
                    </div>

                    <div className="flex items-end">
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={params.save_report}
                                onChange={(e) => setParams({ ...params, save_report: e.target.checked })}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">Save Report</span>
                        </label>
                    </div>
                </div>

                <button
                    onClick={generateReport}
                    disabled={generating}
                    className="w-full md:w-auto flex items-center justify-center space-x-2 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {generating ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                    <span>{generating ? 'Generating...' : 'Generate Report'}</span>
                </button>

                {error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">{error}</p>
                    </div>
                )}
            </div>

            {/* Generated Report */}
            {report && (
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center space-x-2 mb-4">
                        <FileText className="w-5 h-5 text-green-500" />
                        <h3 className="text-lg font-semibold text-gray-900">AI Risk Analysis</h3>
                    </div>

                    {/* Report Metadata */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-md">
                        <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500">Generated</p>
                                <p className="text-sm font-medium">{formatDate(report.generated_at)}</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2">
                            <User className="w-4 h-4 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500">Account</p>
                                <p className="text-sm font-medium">{report.account_id}</p>
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500">Parameters</p>
                            <p className="text-sm font-medium">
                                {(report.parameters?.alpha * 100).toFixed(0)}% VaR, {report.parameters?.lookback_days}d
                            </p>
                        </div>
                    </div>

                    {/* Report Content */}
                    <div className="prose max-w-none">
                        <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                            {report.summary}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-3 mt-6 pt-4 border-t">
                        <button
                            onClick={() => navigator.clipboard.writeText(report.summary)}
                            className="text-sm text-blue-600 hover:text-blue-700"
                        >
                            Copy to Clipboard
                        </button>
                        <button
                            onClick={() => {
                                const blob = new Blob([report.summary], { type: 'text/plain' })
                                const url = URL.createObjectURL(blob)
                                const a = document.createElement('a')
                                a.href = url
                                a.download = `risk-report-${new Date().toISOString().split('T')[0]}.txt`
                                a.click()
                                URL.revokeObjectURL(url)
                            }}
                            className="text-sm text-green-600 hover:text-green-700"
                        >
                            Download Report
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}