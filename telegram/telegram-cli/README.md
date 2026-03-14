# telegram-cli

Command-line tool for reading Telegram channels and groups, writing their content to local files for offline synchronization, and posting messages to specified groups or channels.

## Overview

`telegram-cli` is a terminal-based application that provides:

- **Reading** messages from Telegram channels and groups
- **Exporting** message content to local files for backup and offline processing
- **Writing** new messages or prepared posts to specified Telegram groups or channels
- **Synchronization** of content between local storage and Telegram

This tool depends on [telegram-lib](../telegram-lib/) for all Telegram API interactions.

## Planned Features

- Read messages from multiple channels/groups in a single run
- Export messages to structured local files (JSON, Markdown)
- Filter messages by date range, author, content type
- Compose and post messages from local files
- Schedule message publishing
- Interactive and batch (non-interactive) modes

## Dependencies

| Dependency                                      | Purpose                           |
|-------------------------------------------------|-----------------------------------|
| [telegram-lib](../telegram-lib/)                | Telegram API integration          |

## Prerequisites

- Python 3.11+
- Telegram credentials (see [telegram-lib setup](../telegram-lib/README.md#telegram-credentials-setup))

## Current Status

**Version:** TBD — under development.

## License

MIT
