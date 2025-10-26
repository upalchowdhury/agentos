interface StatCardProps {
  title: string;
  value: string | number;
  change: string;
  isPositive?: boolean;
}

export function StatCard({ title, value, change, isPositive = true }: StatCardProps) {
  return (
    <div className="flex flex-col gap-2 rounded-xl p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
      <p className="text-gray-500 dark:text-gray-400 text-base font-medium leading-normal">
        {title}
      </p>
      <p className="text-gray-900 dark:text-white text-3xl font-bold leading-tight">{value}</p>
      <p
        className={`text-base font-medium leading-normal ${
          isPositive ? 'text-green-500' : 'text-red-500'
        }`}
      >
        {change}
      </p>
    </div>
  );
}
