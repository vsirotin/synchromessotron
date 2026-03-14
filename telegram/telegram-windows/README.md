# telegram-windows

Windows desktop application for Telegram channel reading, message backup, and offline post preparation.

## Overview

This subproject contains the configuration and documentation needed for the **GitHub Action `create-telegram-windows`**, which builds a Windows executable (`.exe`) with the full functionality of [telegram-web](../telegram-web/).

The application is built using a desktop wrapper (e.g., Electron or PyInstaller) around the `telegram-web` frontend and backend, packaged as a standalone Windows installer.

## For End Users

### Download

The latest Windows installer can be downloaded from the [Releases](https://github.com/vsirotin/synchromessotron/releases) page of this repository. Look for the asset named `synchromessotron-telegram-setup.exe`.

### System Requirements

- Windows 10 or later (64-bit)
- Internet connection for Telegram API access

### Installation

1. Download the `.exe` installer from the Releases page.
2. Run the installer and follow the on-screen instructions.
3. Launch "Synchromessotron Telegram" from the Start Menu or Desktop shortcut.
4. On first launch, enter your Telegram credentials (see [telegram-lib credentials setup](../telegram-lib/README.md#telegram-credentials-setup)).

### Features

- Browse and search Telegram channels and groups
- Export messages to local files for offline access
- Compose and publish posts to Telegram
- Automatic synchronization and backup

## For Developers

### GitHub Action

The `create-telegram-windows` GitHub Action:

1. Checks out the repository
2. Builds the `telegram-web` frontend and backend
3. Packages the application as a Windows `.exe` using the desktop wrapper
4. Uploads the installer as a release asset

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
