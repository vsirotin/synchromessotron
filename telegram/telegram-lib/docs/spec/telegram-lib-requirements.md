# Requirements for Sub-Project telegram-lib

This document describes the functional and technical requirements for the sub-project telegram-lib — a part of the Synchromessotron project that enables backup, communication, and content synchronisation with the Telegram messenger.

## Structural Requirements

Telegram-lib is a library of stateless Python functions that provides functionality for other sub-projects such as telegram-cli or telegram-web. These sub-projects are the callers of telegram-lib.

## Functional Requirements

The library provides the following capabilities for Telegram dialogs, groups, and channels in which the user participates:

- F1. Full and incremental backup of message history.
- F2. Sending messages on behalf of the user's account.
- F3. Editing and resending the user's own messages.
- F4. Deleting the user's own messages.
- F5. Retrieving the complete history of the user's dialogs, groups, and channels.
- F6. Downloading individual messages, photos, and media files.
- F7. Checking the availability of Telegram.
- F8. Validating the current (given) user session.
- F9. Returning the library version as a JSON-serialisable object with the same structure as `src/version.yaml` (fields: `version`, `build`, `datetime`).

## Technical Requirements

- T1. The library uses the open-source [Telethon](https://docs.telethon.dev/en/stable/quick-references/client-reference.html) library and, when needed, the [Telegram API](https://core.telegram.org/#tdlib-build-your-own-telegram) directly.
- T2. Because the functions are stateless, the library may provide two or more functions to implement a single functional requirement (e.g., a backup may require many calls with pauses between them).
- T3. The library catches all exceptions and returns its own error object containing an error code and additional information (e.g., the required cooldown time when rate limits are exceeded). Callers of telegram-lib never see the original exceptions of the underlying libraries.
- T4. Each library function is a wrapper around the corresponding Telegram API function. As a wrapper, it logs the input parameters and start timestamp before execution, and the result and end timestamp after execution.
- T5. Logging is configurable by the caller through standard centralised mechanisms (Python `logging` module).
- T6. Every function returns either a payload object or an error object.
- T7. Unlike the raw Telegram API response objects, a payload object contains only the information items that are actually needed by the caller to fulfil the corresponding functional requirement.
- T8. Function signatures, input parameters, and return objects must be clearly and thoroughly documented.
- T9. Documentation uses the original Telegram terminology. Special terms (e.g., the specific meaning of "dialog" in the Telegram API) are explicitly explained.
- T10. Unit tests cover not only the individual functionality under test, but also explicitly demonstrate how the function calls satisfy each functional requirement.
- T11. During implementation, developers should study not only the specification of each called function, but also its source code (when available) in order to handle undocumented exceptions.


