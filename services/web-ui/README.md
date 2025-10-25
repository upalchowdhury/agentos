# Agent Economy OS - Web UI

Production-ready React dashboard for managing Agent Economy OS.

## Features

- **Dashboard**: Real-time metrics and agent monitoring
- **Agent Registry**: Browse and manage registered agents
- **Register Agent**: Onboard new agents with full configuration
- **API Integration**: Direct connection to all backend services

## Development

```bash
# Install dependencies
npm install

# Start dev server (with API proxy)
npm run dev

# Access at http://localhost:3001
```

## API Connections

The UI connects to backend services via proxy:

- `/api/gateway` → Gateway Service (port 8080)
- `/api/identity` → Identity Service (port 3000)
- `/api/memory` → Memory Service (port 8000)
- `/api/policy` → Policy Engine (port 8081)

## Build for Production

```bash
npm run build
```

## Docker Deployment

```bash
docker build -t agentos/web-ui .
docker run -p 3001:80 agentos/web-ui
```

## Environment Variables

Set these in production:

- `VITE_API_URL` - Base API URL (default: /api)
- `VITE_GATEWAY_URL` - Gateway service URL
- `VITE_IDENTITY_URL` - Identity service URL
- `VITE_MEMORY_URL` - Memory service URL
- `VITE_POLICY_URL` - Policy engine URL
