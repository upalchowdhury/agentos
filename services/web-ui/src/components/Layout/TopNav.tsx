export function TopNav() {
  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-gray-200 dark:border-gray-800 px-6 py-4 bg-gray-50 dark:bg-gray-900 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <h2 className="text-gray-900 dark:text-white text-lg font-bold leading-tight tracking-tight">
          Agent Economy OS
        </h2>
      </div>
      <div className="flex flex-1 justify-end items-center gap-4">
        <label className="relative flex-col min-w-40 h-10 max-w-64 hidden md:flex">
          <div className="flex w-full flex-1 items-stretch rounded-lg h-full">
            <div className="text-gray-400 flex border-none bg-gray-100 dark:bg-gray-800 items-center justify-center pl-3 rounded-l-lg">
              <span className="material-symbols-outlined">search</span>
            </div>
            <input
              className="flex w-full min-w-0 flex-1 overflow-hidden rounded-r-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 border-none bg-gray-100 dark:bg-gray-800 h-full placeholder:text-gray-400 px-4 text-base font-normal"
              placeholder="Search"
            />
          </div>
        </label>
        <button className="flex items-center justify-center overflow-hidden rounded-full h-10 w-10 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <div className="bg-blue-600 rounded-full size-10 flex items-center justify-center text-white font-bold">
          JD
        </div>
      </div>
    </header>
  );
}
