# Synchromessotron

A multi-project suite of libraries, command-line tools, web services, and desktop applications for extracting, backing up, and offline processing of messenger content — including preparing new posts for publication.

Synchromessotron covers the full workflow: reading messages from messenger channels and groups, storing them locally, browsing and searching them offline, composing new posts, and publishing them back. It targets multiple messengers and delivery platforms — from terminal CLI to web apps to native desktop executables.

> **Status:** The Telegram core library (`telegram-lib`) is operational with working read/write functionality. Other subprojects are under active development.

---

## Subprojects

| Subproject | Description | README | Version | Release Date |
|---|---|---|---|---|
| **telegram-lib** | Python library for Telegram API integration — reading/writing messages, retry logic, session auth | [README](telegram/telegram-lib/README.md) | 0.1.0 | 2026-03-14 |
| **telegram-cli** | CLI tool for reading Telegram channels/groups, exporting to local files, posting messages | [README](telegram/telegram-cli/README.md) | TBD | TBD |
| **telegram-web** | Web application (Angular SPA + Python backend) for Telegram content management | [README](telegram/telegram-web/README.md) | TBD | TBD |
| **telegram-web-server** | Firebase-hosted deployment of telegram-web | [README](telegram/telegram-web-server/README.md) | TBD | TBD |
| **telegram-windows** | Windows desktop app (.exe) with telegram-web functionality, built via GitHub Action | [README](telegram/telegram-windows/README.md) | TBD | TBD |
| **telegram-macos** | macOS desktop app with telegram-web functionality, built via GitHub Action | [README](telegram/telegram-macos/README.md) | TBD | TBD |
| **vkontakte** | VK.com (VKontakte) integration — structure to be defined | [README](vkontakte/README.md) | TBD | TBD |

---

## License

MIT
