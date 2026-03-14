# telegram-macos

macOS desktop application for Telegram channel reading, message backup, and offline post preparation.

## Overview

This subproject contains the configuration and documentation needed for the **GitHub Action `create-telegram-macos`**, which builds a macOS application with the full functionality of [telegram-web](../telegram-web/).

The application is built using a desktop wrapper (e.g., Electron or PyInstaller) around the `telegram-web` frontend and backend, packaged as a standalone macOS app bundle.

## For End Users

### Download

The latest macOS application can be downloaded from the [Releases](https://github.com/vsirotin/synchromessotron/releases) page of this repository. Look for the asset named `synchromessotron-telegram-macos.dmg` (or `.zip`).

### System Requirements

- macOS 12 (Monterey) or later
- Internet connection for Telegram API access

### Installation

1. Download the `.dmg` file from the Releases page.
2. Open the `.dmg` and drag "Synchromessotron Telegram" to your Applications folder.
3. Launch the application from Applications or Spotlight.
4. On first launch, enter your Telegram credentials (see [telegram-lib credentials setup](../telegram-lib/README.md#telegram-credentials-setup)).

> **Note:** On first launch, macOS may show a security warning. Go to **System Settings → Privacy & Security** and click "Open Anyway".

### Features

- Browse and search Telegram channels and groups
- Export messages to local files for offline access
- Compose and publish posts to Telegram
- Automatic synchronization and backup

## For Developers

### GitHub Action

The `create-telegram-macos` GitHub Action:

1. Checks out the repository
2. Builds the `telegram-web` frontend and backend
3. Packages the application as a macOS `.app` bundle
4. Signs and notarizes the application (if certificates are configured)
5. Uploads the installer as a release asset

### Build Configuration

Build configuration and packaging scripts are located in this directory.

## Dependencies

| Dependency                                      | Purpose                                |
|-------------------------------------------------|----------------------------------------|
| [telegram-web](../telegram-web/)                | Application source                     |

## Current Status

**Version:** TBD — under development.

## License

MIT
