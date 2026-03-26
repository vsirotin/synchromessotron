# Synchromessotron

A multi-project suite of libraries, command-line tools, web services, and desktop applications for extracting, backing up, and offline processing of messenger content — including preparing new posts for publication.

---

## Subprojects

| Subproject | Description | README | 
|---|---|---|
| **telegram-lib** | Python library for Telegram API integration — reading/writing messages, retry logic, session auth | [README](telegram/telegram-lib/README.md) | 
| **telegram-cli** | CLI tool for reading Telegram channels/groups, exporting to local files, posting messages | [README](telegram/telegram-cli/README.md) | 


---

## Working with GitHub Copilot Agent

This project uses [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot) for AI-assisted development.

### Can I close VS Code and shut down my computer once I start a session?

**Yes.** GitHub Copilot Agent sessions run entirely on GitHub's cloud infrastructure. Once you start a session — whether from VS Code, the GitHub web interface, or another supported tool — the agent works autonomously on GitHub's servers. Your local machine and VS Code are **not required** for the session to continue.

You can safely:
- Close VS Code
- Shut down or sleep your computer
- Disconnect from the internet

The agent will continue working in the cloud and commit its changes to the pull request branch. You can check progress at any time by opening the pull request on GitHub — no local connection required.

When the agent finishes (or needs your input), you will see updates in the pull request.

---

## License

MIT
