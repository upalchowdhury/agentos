import { Link, useLocation } from 'react-router-dom'
import { Activity, BarChart3, BoxSelect, FileText, Home, Zap } from 'lucide-react'

export default function Layout({ children }) {
  const location = useLocation()
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Traces', href: '/traces', icon: Activity },
    { name: 'Agents', href: '/agents', icon: Zap },
    { name: 'Metrics', href: '/metrics', icon: BarChart3 },
    { name: 'Logs', href: '/logs', icon: FileText },
  ]
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BoxSelect className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AgentOS</h1>
                <p className="text-sm text-gray-500">Observability & Runtime Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <span className="w-2 h-2 bg-green-600 rounded-full mr-1.5"></span>
                All Systems Operational
              </span>
            </div>
          </div>
        </div>
      </header>
      
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center space-x-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors
                    ${isActive 
                      ? 'border-blue-600 text-blue-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
