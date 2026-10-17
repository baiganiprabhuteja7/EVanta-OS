# EVanta OS

EVanta OS is an EV charging intelligence and business management platform.

**Powering Mobility. Engineering Intelligence.**

The project includes a responsive application shell, shared design system, and
an illustrative dashboard. The remaining product routes are placeholders.
Dashboard readings are deterministic demo data; backend integration is not
included.

## Getting started

From the `frontend` directory, install dependencies and start the Vite server:

```sh
npm install
npm run dev
```

Vite prints the local URL after startup.

## Available routes

- `/dashboard`
- `/stations`
- `/chargers`
- `/energy`
- `/analytics`
- `/sessions`
- `/settings`

The Dashboard route includes date-filtered energy, revenue, and session charts;
a charger status breakdown; station and charging-session tables; simulated
operational alerts; and navigation shortcuts. Dashboard data is generated from
the frontend-only fixture in `src/data/dashboardData.js`. The date selector
supports today, the last 7 days, and the last 30 days. Refresh regenerates the
illustrative readings; it does not connect to live equipment.
Other routes currently render a shared page header and placeholder content.

## Project structure

- `src/components/common/` — shared UI components
- `src/components/layout/` — application shell, sidebar, and topbar
- `src/data/` — navigation metadata and demo dashboard data
- `src/pages/` — route-level pages
- `src/utils/` — shared formatters
- `src/App.jsx` — route declarations
- `src/index.css` and `src/App.css` — design tokens and application styling

## Validation

```sh
npm run build
npm run lint
```
