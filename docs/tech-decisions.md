# Technology Decisions

> Fill this in at Human Checkpoint 1 (see `project-plan.md`).

## Telegram Library

- **Decision:** **Telethon**
- **Options considered:** Telethon (recommended), python-telegram-bot (bot-only — unsuitable)
- **Rationale:** Telethon uses the MTProto protocol and works with full user accounts, which is required to read and forward personal messages. `python-telegram-bot` is bot-only and cannot access user account messages.

## VK Library

- **Decision:** **vk_api**
- **Options considered:** `vk_api` (recommended), `vkbottle`
- **Rationale:** `vk_api` is stable, widely used, and has comprehensive coverage of the VK API including the `messages` group required for reading and sending messages under a user account.

## Sync-State Storage

- **Decision:** **Firestore**
- **Options considered:** Firestore (recommended — native Firebase integration)
- **Rationale:** Firestore is the native persistent storage solution for Firebase Cloud Functions, requires no extra infrastructure, and provides atomic reads/writes with a simple SDK.

## Notes

_Decided at Human Checkpoint 1 on 10 March 2026._
