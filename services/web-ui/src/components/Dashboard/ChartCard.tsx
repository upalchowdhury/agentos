interface ChartCardProps {
  title: string;
  value: string | number;
  timeRange: string;
  change: string;
}

export function ChartCard({ title, value, timeRange, change }: ChartCardProps) {
  return (
    <div className="flex flex-col gap-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
      <p className="text-gray-900 dark:text-white text-base font-medium leading-normal">{title}</p>
      <p className="text-gray-900 dark:text-white text-[32px] font-bold leading-tight truncate">
        {value}
      </p>
      <div className="flex gap-1">
        <p className="text-gray-500 dark:text-gray-400 text-base font-normal leading-normal">
          {timeRange}
        </p>
        <p className="text-green-500 text-base font-medium leading-normal">{change}</p>
      </div>
      <div className="flex min-h-[220px] flex-1 flex-col gap-8 py-4">
        <svg
          fill="none"
          height="100%"
          preserveAspectRatio="none"
          viewBox="0 0 475 150"
          width="100%"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25V149H0V109Z"
            fill="url(#paint0_linear_chart)"
          />
          <path
            d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25"
            stroke="#3B82F6"
            strokeLinecap="round"
            strokeWidth="3"
          />
          <defs>
            <linearGradient
              gradientUnits="userSpaceOnUse"
              id="paint0_linear_chart"
              x1="236"
              x2="236"
              y1="1"
              y2="149"
            >
              <stop stopColor="#3B82F6" stopOpacity="0.3" />
              <stop offset="1" stopColor="#3B82F6" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
