import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'Risk Dashboard',
    description: 'AI-Driven Portfolio Risk Management Platform',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <div className="min-h-screen bg-gray-50">
                    <nav className="bg-white shadow-sm border-b">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div className="flex justify-between h-16">
                                <div className="flex items-center">
                                    <h1 className="text-xl font-semibold text-gray-900">
                                        Risk Dashboard
                                    </h1>
                                </div>
                                <div className="flex items-center space-x-4">
                                    <a href="/dashboard" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                        Dashboard
                                    </a>
                                    <a href="/positions" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                        Positions
                                    </a>
                                    <a href="/risk" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                        Risk
                                    </a>
                                    <a href="/reports" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                                        Reports
                                    </a>
                                </div>
                            </div>
                        </div>
                    </nav>
                    <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                        {children}
                    </main>
                </div>
            </body>
        </html>
    )
}