# telegram-web-server

Firebase-hosted server deployment of the [telegram-web](../telegram-web/) application.

## Overview

`telegram-web-server` packages and deploys the `telegram-web` application (both frontend and backend) to Firebase, providing:

- **Firebase Hosting** for the Angular SPA frontend
- **Firebase Cloud Functions** for the Python backend API
- **Firestore** for persistent state and message storage
- **Firebase Authentication** (optional) for access control
- Scheduled Cloud Functions for automatic synchronization

## Architecture

```
Firebase Project
├── Hosting           ← Angular SPA (static files)
├── Cloud Functions   ← Python backend API
└── Firestore         ← Sync state & message cache
```

## Dependencies

| Dependency                                      | Purpose                               |
|-------------------------------------------------|---------------------------------------|
| [telegram-web](../telegram-web/)                | Application source (frontend+backend) |
| Firebase CLI                                    | Deployment tooling                    |
| Firebase project                                | Cloud infrastructure                  |

## Prerequisites

- Node.js / npm (LTS) for Firebase CLI
- Firebase CLI (`npm install -g firebase-tools`)
- A Firebase project with Firestore enabled
- Python 3.11+

## Current Status

**Version:** TBD — under development.

## License

MIT
