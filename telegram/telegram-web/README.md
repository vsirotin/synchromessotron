# telegram-web

Web application for reading Telegram channels/groups, managing local backups, and composing posts — delivered as an Angular SPA with a Python backend.

## Overview

`telegram-web` provides a browser-based interface for all the functionality of [telegram-cli](../telegram-cli/), including:

- Browse and search messages from Telegram channels and groups
- View and manage locally exported message archives
- Compose and publish new posts to Telegram
- Visual timeline and filtering of synchronized content

## Architecture

```
telegram-web/
├── frontend/    # Angular SPA (TypeScript)
└── backend/     # Python API server using telegram-cli
```

### Frontend

An Angular single-page application providing the user interface. Communicates with the backend via REST API.

**Planned technology stack:**
- Angular 17+
- TypeScript
- Angular Material or Tailwind CSS for UI components

### Backend

A Python API server that wraps [telegram-cli](../telegram-cli/) functionality and exposes it as HTTP endpoints for the frontend.

**Planned technology stack:**
- FastAPI or Flask
- Python 3.11+
- Depends on [telegram-cli](../telegram-cli/)

## Dependencies

| Dependency                                      | Purpose                              |
|-------------------------------------------------|--------------------------------------|
| [telegram-cli](../telegram-cli/)                | Core Telegram read/write operations  |
| [telegram-lib](../telegram-lib/)                | Telegram API integration (transitive)|

## Current Status

**Version:** TBD — under development.

## License

MIT
