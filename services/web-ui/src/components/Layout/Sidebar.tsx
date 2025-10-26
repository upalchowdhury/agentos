import { Link, useLocation } from 'react-router-dom';

interface NavItem {
  name: string;
  icon: string;
  path: string;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', icon: 'dashboard', path: '/' },
  { name: 'Agents', icon: 'support_agent', path: '/agents' },
  { name: 'Deployments', icon: 'rocket_launch', path: '/deployments' },
  { name: 'Invocations', icon: 'double_arrow', path: '/invocations' },
  { name: 'Logs', icon: 'receipt_long', path: '/logs' },
  { name: 'Metrics', icon: 'monitoring', path: '/metrics' },
  { name: 'Settings', icon: 'settings', path: '/settings' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="flex flex-col w-64 bg-gray-50 dark:bg-gray-900 text-gray-300">
      <div className="flex items-center gap-3 p-5 border-b border-gray-200 dark:border-gray-800">
        <div className="bg-blue-600 rounded-full size-10 flex items-center justify-center text-white font-bold">
          JD
        </div>
        <div className="flex flex-col">
          <h1 className="text-gray-900 dark:text-white text-base font-medium leading-normal">
            John Doe
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm font-normal leading-normal">
            john.doe@email.com
          </p>
        </div>
      </div>

      <nav className="flex-1 px-2 py-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-600 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <span className="material-symbols-outlined text-xl">{item.icon}</span>
              <span className="text-sm font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <Link
          to="/deploy"
          className="flex w-full items-center justify-center rounded-lg h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-colors"
        >
          <span className="truncate">Deploy Agent</span>
        </Link>
      </div>
    </aside>
  );
}
