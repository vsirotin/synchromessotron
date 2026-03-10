# Synchromessotron — Project Requirements

## Functional Requirements

The goal of the project is to develop a service that will be launched as a cron job on Firebase.
The project will be a well-documented open-source project on GitHub.

On each start, the service performs content synchronization between two or more accounts in one or two messengers (e.g. Telegram and VK.com). Pre-condition: the owner of the service is a human who has accounts in all synchronized messengers.

### Core Abstractions

The core of the service works with an abstract model of messengers and accounts. Concrete data should be configurable.

The main elements of the abstraction are:

- **Messenger** — represents a messaging platform
- **Reader** — reads messages from a messenger account
- **Writer** — writes messages to a messenger account

### Sync Algorithm

Let's imagine that in our "world" there are two Messengers (together with the owner's accounts): A and B.
There are Readers and Writers for both:

- `Ra` — Reader for A
- `Wa` — Writer for A
- `Rb` — Reader for B
- `Wb` — Writer for B

The service works as follows. After starting, it reads from external storage (since this is a serverless service) the time of the last synchronization. After that, the service processes the following steps:

1. `Ra` reads new content from A since the last synchronization time (producing a list of messages `La`).
2. `Rb` reads new content from B since the last synchronization time (producing a list of messages `Lb`).
3. `Wb` writes messages from `La` to B.
4. `Wa` writes messages from `Lb` to A.
5. The service updates the time of the last synchronization in external storage.

---

## Implementation Requirements

- Details about the writing process are configurable (e.g. in Telegram it can be "Forwarding" under the owner's account).
- The core code should use the concept of interfaces for Readers and Writers, so that it can be easily extended to support new messengers in the future.
- The service should handle potential errors gracefully, such as network issues or API rate limits, and log relevant information for debugging purposes.

### Documentation

The project documentation should include:

- **README.md** — clear instructions on how to set up and configure the service.
- **DEVELOPMENT.md** — detailed information for developers, as well as examples of how to add support for new messengers.

---

## Requirements for the Planning and Development Process

The project should be mostly developed by AI agents.

The following checkpoints for human-in-the-loop should be planned:

1. The decision about the tools (libraries, frameworks) for Readers and Writers for Telegram and VK.com should be made by a human. (Telethon for Telegram can be a good choice.)
2. After implementation of the core and Readers/Writers for Telegram and VK.com, a human should review the code and test the service to ensure it works as expected.
3. The first version should be testable locally using the Firebase emulator.
4. After that, it should be deployed to Firebase and tested in a production environment.
