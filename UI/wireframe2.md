<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Agent Economy OS Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#007BFF",
                        "background-light": "#f6f7f8",
                        "background-dark": "#121212",
                        "component-dark": "#1E1E1E",
                        "border-dark": "#2E2E2E"
                    },
                    fontFamily: {
                        "display": ["Inter", "sans-serif"]
                    },
                    borderRadius: {
                        "DEFAULT": "0.5rem",
                        "lg": "1rem",
                        "xl": "1.5rem",
                        "full": "9999px"
                    },
                },
            },
        }
    </script>
</head>
<body class="bg-background-light dark:bg-background-dark font-display">
<div class="flex h-screen">
<!-- SideNavBar -->
<aside class="flex flex-col w-64 bg-background-light dark:bg-component-dark text-gray-300">
<div class="flex items-center gap-3 p-5 border-b border-gray-200 dark:border-border-dark">
<div class="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" data-alt="John Doe's profile picture" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuBv-hxE9FkgDrb1ffV_Pdi6-cuJSSaNZOMI3haFR2avu-ixmVsb_Lp9xtmA1H35JJPLl44Q2vOUDTFMgr1TgJOV2R29BOVKAI0-xj4yEGiQybEq0_Ek8KDD8ZDahx1uv-PYfZ8oBg5l0qUKlABwOR8h6aWHnmVapoTcKAJhPdsEnenI4QJnbNu-9sFSoPpQiv5UYzUsq2Zv5L2F9eFJh40A7vxQ0HePTUX297OuHYQDOjyyWCb9niXvKZdrseqvuAYBFwEBEUzEGP4");'></div>
<div class="flex flex-col">
<h1 class="text-gray-900 dark:text-white text-base font-medium leading-normal">John Doe</h1>
<p class="text-gray-500 dark:text-gray-400 text-sm font-normal leading-normal">john.doe@email.com</p>
</div>
</div>
<nav class="flex-1 px-2 py-4 space-y-2">
<a class="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/20 text-primary" href="#">
<span class="material-symbols-outlined">dashboard</span>
<span class="text-sm font-medium">Dashboard</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">support_agent</span>
<span class="text-sm font-medium">Agents</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">rocket_launch</span>
<span class="text-sm font-medium">Deployments</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">double_arrow</span>
<span class="text-sm font-medium">Invocations</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">receipt_long</span>
<span class="text-sm font-medium">Logs</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">monitoring</span>
<span class="text-sm font-medium">Metrics</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700" href="#">
<span class="material-symbols-outlined">settings</span>
<span class="text-sm font-medium">Settings</span>
</a>
</nav>
<div class="p-4 border-t border-gray-200 dark:border-border-dark">
<button class="flex w-full min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
<span class="truncate">Deploy Agent</span>
</button>
</div>
</aside>
<!-- Main Content -->
<div class="flex flex-col flex-1 overflow-y-auto">
<!-- TopNavBar -->
<header class="flex items-center justify-between whitespace-nowrap border-b border-gray-200 dark:border-border-dark px-6 py-4 bg-background-light dark:bg-background-dark sticky top-0 z-10">
<div class="flex items-center gap-4">
<h2 class="text-gray-900 dark:text-white text-lg font-bold leading-tight tracking-[-0.015em]">Agent Economy OS</h2>
</div>
<div class="flex flex-1 justify-end items-center gap-4">
<label class="relative flex-col min-w-40 !h-10 max-w-64 hidden md:flex">
<div class="flex w-full flex-1 items-stretch rounded-lg h-full">
<div class="text-gray-400 flex border-none bg-gray-100 dark:bg-component-dark items-center justify-center pl-3 rounded-l-lg border-r-0">
<span class="material-symbols-outlined">search</span>
</div>
<input class="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-r-lg text-gray-900 dark:text-white focus:outline-0 focus:ring-0 border-none bg-gray-100 dark:bg-component-dark h-full placeholder:text-gray-400 px-4 text-base font-normal leading-normal" placeholder="Search" value=""/>
</div>
</label>
<button class="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 w-10 bg-gray-100 dark:bg-component-dark text-gray-900 dark:text-white text-sm font-bold leading-normal tracking-[0.015em]">
<span class="material-symbols-outlined">notifications</span>
</button>
<div class="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" data-alt="User profile picture" style='background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuDDU_gVmHYl9n4eA9vouVmknazOEaXzodFve-WBRvOv7GVvK_iORpaPp3xJyqFTV0b_BjyUjqV4dzD9ZfVv-FNXd0mBDtwImrZ2RASarcroaJJJ0h7yHvwyicIogO6McP1Wji1yZzJEs7DvdSaOL6gOw6j4wgDT4nd_OMJh23lc8c20PjwzHxoBKTDT1VrZDvQ1kd8uVTIUnA5NTYzL9pgwOfOtdTFqmechshf80rkX6XEnWL538V7qyJE6coJQyDTouxl8KaueXYA");'></div>
</div>
</header>
<main class="flex-1 p-6">
<!-- PageHeading -->
<div class="flex flex-wrap justify-between items-center gap-3 mb-6">
<p class="text-gray-900 dark:text-white text-3xl font-black leading-tight tracking-[-0.033em]">Dashboard</p>
<div class="flex items-center gap-4">
<button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-gray-200 dark:bg-component-dark text-gray-900 dark:text-white text-sm font-bold leading-normal tracking-[0.015em]">
<span class="truncate">View All Agents</span>
</button>
<button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
<span class="truncate">Deploy Agent</span>
</button>
</div>
</div>
<!-- Stats -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
<div class="flex flex-col gap-2 rounded-xl p-6 bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark">
<p class="text-gray-500 dark:text-gray-400 text-base font-medium leading-normal">Total Agents</p>
<p class="text-gray-900 dark:text-white tracking-light text-3xl font-bold leading-tight">12</p>
<p class="text-green-500 text-base font-medium leading-normal">+10%</p>
</div>
<div class="flex flex-col gap-2 rounded-xl p-6 bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark">
<p class="text-gray-500 dark:text-gray-400 text-base font-medium leading-normal">Active Deployments</p>
<p class="text-gray-900 dark:text-white tracking-light text-3xl font-bold leading-tight">5</p>
<p class="text-green-500 text-base font-medium leading-normal">+5%</p>
</div>
<div class="flex flex-col gap-2 rounded-xl p-6 bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark">
<p class="text-gray-500 dark:text-gray-400 text-base font-medium leading-normal">Total Invocations</p>
<p class="text-gray-900 dark:text-white tracking-light text-3xl font-bold leading-tight">1,234</p>
<p class="text-green-500 text-base font-medium leading-normal">+20%</p>
</div>
<div class="flex flex-col gap-2 rounded-xl p-6 bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark">
<p class="text-gray-500 dark:text-gray-400 text-base font-medium leading-normal">Total Cost</p>
<p class="text-gray-900 dark:text-white tracking-light text-3xl font-bold leading-tight">$5,678.90</p>
<p class="text-green-500 text-base font-medium leading-normal">+15%</p>
</div>
</div>
<!-- Charts -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
<div class="flex flex-col gap-2 rounded-xl bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark p-6">
<p class="text-gray-900 dark:text-white text-base font-medium leading-normal">Invocations (Last 30 Days)</p>
<p class="text-gray-900 dark:text-white tracking-light text-[32px] font-bold leading-tight truncate">1,234</p>
<div class="flex gap-1">
<p class="text-gray-500 dark:text-gray-400 text-base font-normal leading-normal">Last 30 Days</p>
<p class="text-green-500 text-base font-medium leading-normal">+20%</p>
</div>
<div class="flex min-h-[220px] flex-1 flex-col gap-8 py-4">
<svg fill="none" height="100%" preserveaspectratio="none" viewbox="0 0 475 150" width="100%" xmlns="http://www.w3.org/2000/svg">
<path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25V149H0V109Z" fill="url(#paint0_linear_chart)"></path>
<path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25" stroke="#007BFF" stroke-linecap="round" stroke-width="3"></path>
<defs>
<lineargradient gradientunits="userSpaceOnUse" id="paint0_linear_chart" x1="236" x2="236" y1="1" y2="149">
<stop stop-color="#007BFF" stop-opacity="0.3"></stop>
<stop offset="1" stop-color="#007BFF" stop-opacity="0"></stop>
</lineargradient>
</defs>
</svg>
</div>
</div>
<div class="flex flex-col gap-2 rounded-xl bg-gray-100 dark:bg-component-dark border border-gray-200 dark:border-border-dark p-6">
<p class="text-gray-900 dark:text-white text-base font-medium leading-normal">Cost (Last 30 Days)</p>
<p class="text-gray-900 dark:text-white tracking-light text-[32px] font-bold leading-tight truncate">$5,678.90</p>
<div class="flex gap-1">
<p class="text-gray-500 dark:text-gray-400 text-base font-normal leading-normal">Last 30 Days</p>
<p class="text-green-500 text-base font-medium leading-normal">+15%</p>
</div>
<div class="flex min-h-[220px] flex-1 flex-col gap-8 py-4">
<svg fill="none" height="100%" preserveaspectratio="none" viewbox="0 0 475 150" width="100%" xmlns="http://www.w3.org/2000/svg">
<path d="M0 65C18.1538 65 18.1538 129 36.3077 129C54.4615 129 54.4615 89 72.6154 89C90.7692 89 90.7692 37 108.923 37C127.077 37 127.077 97 145.231 97C163.385 97 163.385 29 181.538 29C199.692 29 199.692 69 217.846 69C236 69 236 85 254.154 85C272.308 85 272.308 9 290.462 9C308.615 9 308.615 1 326.769 1C344.923 1 344.923 149 363.077 149C381.231 149 381.231 59 399.385 59C417.538 59 417.538 105 435.692 105C453.846 105 453.846 125 472 125V149H0V65Z" fill="url(#paint0_linear_chart)"></path>
<path d="M0 65C18.1538 65 18.1538 129 36.3077 129C54.4615 129 54.4615 89 72.6154 89C90.7692 89 90.7692 37 108.923 37C127.077 37 127.077 97 145.231 97C163.385 97 163.385 29 181.538 29C199.692 29 199.692 69 217.846 69C236 69 236 85 254.154 85C272.308 85 272.308 9 290.462 9C308.615 9 308.615 1 326.769 1C344.923 1 344.923 149 363.077 149C381.231 149 381.231 59 399.385 59C417.538 59 417.538 105 435.692 105C453.846 105 453.846 125 472 125" stroke="#007BFF" stroke-linecap="round" stroke-width="3"></path>
</svg>
</div>
</div>
</div>
<!-- Recent Invocations Table -->
<div class="bg-gray-100 dark:bg-component-dark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
<h3 class="text-gray-900 dark:text-white text-lg font-bold p-6">Recent Invocations</h3>
<div class="overflow-x-auto">
<table class="w-full text-left">
<thead class="bg-gray-50 dark:bg-gray-800/50">
<tr>
<th class="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Agent</th>
<th class="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Deployment</th>
<th class="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Timestamp</th>
<th class="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400">Status</th>
<th class="p-4 text-sm font-semibold text-gray-500 dark:text-gray-400"></th>
</tr>
</thead>
<tbody class="divide-y divide-gray-200 dark:divide-border-dark">
<tr>
<td class="p-4 text-sm text-gray-900 dark:text-white font-medium">Auto-Responder</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">dep_1a2b3c4d</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">2023-10-27 10:30 AM</td>
<td class="p-4">
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300">Success</span>
</td>
<td class="p-4 text-right">
<a class="text-primary font-medium text-sm" href="#">Details</a>
</td>
</tr>
<tr>
<td class="p-4 text-sm text-gray-900 dark:text-white font-medium">Data-Analyzer</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">dep_5e6f7g8h</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">2023-10-27 10:28 AM</td>
<td class="p-4">
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">Failed</span>
</td>
<td class="p-4 text-right">
<a class="text-primary font-medium text-sm" href="#">Details</a>
</td>
</tr>
<tr>
<td class="p-4 text-sm text-gray-900 dark:text-white font-medium">Content-Generator</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">dep_9i0j1k2l</td>
<td class="p-4 text-sm text-gray-500 dark:text-gray-400">2023-10-27 10:25 AM</td>
<td class="p-4">
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300">Success</span>
</td>
<td class="p-4 text-right">
<a class="text-primary font-medium text-sm" href="#">Details</a>
</td>
</tr>
<!-- Empty State Example -->
<!-- <tr>
                                    <td colspan="5" class="text-center p-12">
                                        <div class="flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
                                            <span class="material-symbols-outlined text-6xl">upcoming</span>
                                            <p class="mt-4 text-lg font-medium">No recent invocations</p>
                                            <p class="text-sm">Your latest agent activity will appear here.</p>
                                        </div>
                                    </td>
                                </tr> -->
</tbody>
</table>
</div>
</div>
<!-- Empty State Example -->
<!-- <div class="flex flex-col items-center justify-center text-center p-10 bg-gray-100 dark:bg-component-dark rounded-xl border border-gray-200 dark:border-border-dark mt-6">
                    <span class="material-symbols-outlined text-7xl text-gray-400 dark:text-gray-500">space_dashboard</span>
                    <h3 class="text-xl font-bold text-gray-900 dark:text-white mt-4">Welcome to your Dashboard</h3>
                    <p class="text-gray-500 dark:text-gray-400 mt-2 max-w-md">No invocation data yet. Deploy your first agent to start tracking performance and see your data here.</p>
                    <button class="mt-6 flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
                        <span class="truncate">Deploy Your First Agent</span>
                    </button>
                </div> -->
</main>
</div>
</div>
</body></html>