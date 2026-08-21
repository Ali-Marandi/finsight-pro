# Architecture Overview

FinSight Pro uses a hybrid architecture combining Electron for the desktop shell, React for the UI layer, and a FastAPI Python backend that wraps the existing CLI analysis engine.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Electron Shell                     │
│  ┌───────────────────────────────────────────────┐  │
│  │           React + TypeScript UI                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Dashboard │ │ Analysis │ │   Reports    │  │  │
│  │  │   Page    │ │   Page   │ │    Page      │  │  │
│  │  └────┬─────┘ └────┬─────┘ └──────┬───────┘  │  │
│  │       └────────────┼──────────────┘           │  │
│  │                    │                          │  │
│  │            API Client Layer                    │  │
│  │         (Axios / Fetch)                        │  │
│  └────────────────────┼──────────────────────────┘  │
│                       │ IPC / HTTP                   │
│  ┌────────────────────┼──────────────────────────┐  │
│  │         FastAPI Backend (Python)               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │  Routers  │ │ Services │ │    Models    │  │  │
│  │  └────┬─────┘ └────┬─────┘ └──────┬───────┘  │  │
│  │       └────────────┼──────────────┘           │  │
│  │                    │                          │  │
│  │         Core Analysis Engine                   │  │
│  │      (wraps src/finsight/*)                    │  │
│  └────────────────────┼──────────────────────────┘  │
│                       │                             │
│  ┌────────────────────┼──────────────────────────┐  │
│  │              SQLite Database                   │  │
│  │        (SQLAlchemy ORM)                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Electron + React**: Cross-platform desktop with web-standard UI tooling
2. **FastAPI Backend**: Reuses existing Python analysis code without rewriting
3. **SQLite**: Zero-config embedded database, perfect for single-user desktop
4. **IPC Bridge**: Electron's IPC for local communication, HTTP fallback for dev

## Data Flow

1. User imports a CSV/XLSX financial statement via the UI
2. React sends file to FastAPI via IPC
3. FastAPI parses the file, runs all 15+ financial ratios
4. Results stored in SQLite for history/caching
5. Results returned to React, rendered as interactive charts and tables
6. User can export reports as PDF, XLSX, or HTML

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `desktop/electron/` | App lifecycle, window management, IPC, auto-updater |
| `desktop/src/renderer/` | All UI: pages, components, hooks, state management |
| `api/app/routers/` | HTTP endpoints for analysis, files, settings |
| `api/app/services/` | Business logic wrapping `src/finsight/` engine |
| `api/app/models/` | SQLAlchemy ORM models and Pydantic schemas |
| `src/finsight/` | Core calculation engine (shared with CLI) |
