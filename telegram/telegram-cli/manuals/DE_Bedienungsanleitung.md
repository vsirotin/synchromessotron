# telegram-cli — Bedienungsanleitung

Diese Anleitung erklärt, wie Sie **telegram-cli** installieren und verwenden — ein Befehlszeilenwerkzeug, mit dem Sie Ihre Telegram-Nachrichten sichern, lesen und verwalten können, ohne die offizielle App. Sie müssen kein Programmierer sein. Folgen Sie einfach den Schritten in der angegebenen Reihenfolge.

---

Telegram ist einer der meistgenutzten Messenger der Welt mit über 900 Millionen monatlich aktiven Nutzern in Dutzenden von Sprachen und Ländern.

| Sprache | ISO 639‑1 | Wichtigste Länder | Geschätzte Telegram-Nutzer |
|---------|-----------|-------------------|---------------------------|
| Russisch | ru | Russland, Ukraine, Belarus | ≈ 120–150 Millionen |
| Englisch | en | Indien, USA, Großbritannien | ≈ 110–130 Millionen |
| Persisch (Farsi) | fa | Iran, Afghanistan, Tadschikistan | ≈ 40–50 Millionen |
| Türkisch | tr | Türkei, Zypern, Deutschland (Diaspora) | ≈ 25–35 Millionen |
| Arabisch | ar | Ägypten, Irak, Saudi-Arabien | ≈ 20–30 Millionen |
| Deutsch | de | Deutschland, Österreich, Schweiz | ≈ 8–12 Millionen |

Telegram ist in bestimmten Ländern oder Regionen manchmal nicht verfügbar oder gesperrt. In diesen Fällen kann telegram-cli helfen — es ermöglicht Ihnen, über die Befehlszeile mit Ihren Telegram-Daten zu arbeiten, unabhängig von den offiziellen Apps.

Das Werkzeug ist besonders nützlich für die **Offline-Verarbeitung** von Telegram-Inhalten — beispielsweise zum Sichern von Gesprächen, Gruppen und Kanälen für spätere Analysen mit KI-Werkzeugen oder zur weiteren Automatisierung.

Sie müssen kein Programmierer sein, um dieses Werkzeug zu verwenden. Folgen Sie einfach den nachstehenden Schritten.

---

## Inhalt

- [Erste Schritte — Windows-Schnellstart](#erste-schritte--windows-schnellstart)
- [Übersicht — Was kann telegram-cli?](#übersicht--was-kann-telegram-cli)
- [Einrichtungs-Checkliste](#einrichtungs-checkliste)
- [Installation](#installation)
- [Sicherheit — Zugangsdaten schützen](#sicherheit--zugangsdaten-schützen)
- [Speicherort der Dateien](#speicherort-der-dateien)
- [Befehlsreferenz](#befehlsreferenz)
- [Fehlerbehandlung](#fehlerbehandlung)
- [Erweiterte Funktionen](#erweiterte-funktionen)
- [Fehlerbehebung](#fehlerbehebung)

---

## Erste Schritte — Windows-Schnellstart

> Dieser Abschnitt richtet sich an **Windows-Nutzer**, die `telegram-cli.exe` heruntergeladen haben. Wenn Sie macOS verwenden oder die Python-Variante nutzen, springen Sie zur [Einrichtungs-Checkliste](#einrichtungs-checkliste).

Hier sind die fünf Befehle, die Sie benötigen, um Ihre erste Sicherung durchzuführen. Jeder Befehl wird weiter unten in dieser Anleitung ausführlich erklärt.

**Bevor Sie beginnen:** Laden Sie `telegram-cli.exe` und dieses Benutzerhandbuch wie in [Installation](#installation) beschrieben herunter. Legen Sie dann `telegram-cli.exe` in einen Ordner Ihrer Wahl — zum Beispiel `C:\Users\IhrName\telegram-cli\`. Öffnen Sie die Eingabeaufforderung in diesem Ordner (siehe [Eingabeaufforderung öffnen](#eingabeaufforderung-öffnen-windows-oder-terminal-macos) weiter unten).

**Schritt 1 — API-Zugangsdaten holen** von <https://my.telegram.org/apps> (einmalig, siehe [Schritt 2](#schritt-2--telegram-anwendung-erstellen) für Details).

**Schritt 2 — Anmelden:**
```
telegram-cli init
```
Geben Sie `api_id`, `api_hash` und Ihre Telefonnummer ein, wenn Sie dazu aufgefordert werden. Tippen Sie den Anmeldecode ein, der an Ihre Telegram-App gesendet wird.

**Schritt 3 — Überprüfen:**
```
telegram-cli whoami
```
Sie sollten Ihren Namen und Ihre Telefonnummer sehen.

**Schritt 4 — Gespräche auflisten:**
```
telegram-cli get-dialogs
```
Finden Sie die ID des Gesprächs, das Sie sichern möchten (die Zahl in der Spalte `ID`).

**Schritt 5 — Sichern:**
```
telegram-cli backup -1001234567890 --limit=500
```
Ersetzen Sie `-1001234567890` durch die tatsächliche ID aus Schritt 4. Ihre Nachrichten werden in einem `synchromessotron\`-Ordner im aktuellen Verzeichnis gespeichert.

> **SmartScreen-Warnung beim ersten Start:** Windows zeigt möglicherweise _„Windows hat Ihren PC geschützt"_ an. Klicken Sie auf **Weitere Informationen** → **Trotzdem ausführen**. Dies geschieht nur einmal.

---

## Übersicht — Was kann telegram-cli?

| Befehl | Funktion |
|--------|----------|
| `init` | Zugangsdaten und Sitzung einrichten |
| `whoami` | Sitzung prüfen und Benutzerinformationen anzeigen |
| `ping` | Telegram-Erreichbarkeit prüfen |
| `get-dialogs` | Gespräche auflisten |
| `backup` | Vollständige oder inkrementelle Nachrichtensicherung |
| `send` | Nachricht an ein Gespräch senden |
| `edit` | Eine zuvor gesendete Nachricht bearbeiten |
| `delete` | Eigene Nachrichten löschen |
| `download-media` | Foto, Video oder Datei aus einer Nachricht herunterladen |
| `help` | Hilfe in Ihrer Sprache anzeigen |
| `version` | Versionsinformationen anzeigen |

> **Was ist ein „Dialog"?** In Telegram bezeichnet „Dialog" jedes Gespräch — einen privaten Chat mit einer Person, einen Gruppenchat oder einen Kanal.

---

## Einrichtungs-Checkliste

Um telegram-cli zu verwenden, führen Sie diese vier Schritte einmalig aus:

- [ ] **Schritt 1** — Datei für Ihre Plattform herunterladen.
- [ ] **Schritt 2** — Telegram-Anwendung erstellen, um API-Zugangsdaten zu erhalten.
- [ ] **Schritt 3** — Sitzung einrichten — telegram-cli meldet Sie an.
- [ ] **Schritt 4** — Überprüfen, ob die Einrichtung funktioniert.

Die folgenden Abschnitte führen Sie durch jeden Schritt im Detail.

---

## Installation

### Schritt 1 — Variante wählen und herunterladen

Gehen Sie zur Seite [Releases](https://github.com/vsirotin/synchromessotron/releases/), suchen Sie die neueste stabile Version, öffnen Sie „Assets" und laden Sie die Datei für Ihre Plattform herunter:

| Plattform | Datei | Zusätzliche Software erforderlich? |
|-----------|-------|------------------------------------|
| **Windows** | `telegram-cli.exe` | Nein |
| **macOS** | `telegram-cli-macos.zip` | Nein |
| **Beliebig (Python)** | `telegram-cli.pyz` | Ja — Python ≥ 3.11 |

Legen Sie die heruntergeladene Datei in einen Ordner Ihrer Wahl — zum Beispiel einen `telegram-cli`-Ordner auf Ihrem Desktop oder in Ihrem Benutzerverzeichnis.

> **Welche Variante soll ich wählen?**
>
> - **Windows oder macOS** — verwenden Sie die plattformspezifische Datei. Keine zusätzliche Software erforderlich.
> - **Python-Variante** — wählen Sie diese, wenn Sie den Code vor der Ausführung prüfen möchten: `.pyz` ist ein standardmäßiges Python-ZIP-Archiv, das Sie öffnen und lesen können. Es funktioniert auch unter Linux.

**Hinweise zum ersten Start je Plattform:**

- **Windows:** Beim ersten Ausführen zeigt SmartScreen möglicherweise _„Windows hat Ihren PC geschützt"_ an. Klicken Sie auf **Weitere Informationen** → **Trotzdem ausführen**. Dies geschieht nur einmal.
- **macOS:** Nach dem Entpacken öffnen Sie das Terminal im Ordner und führen Sie diese zwei Befehle einmalig aus:
  ```
  chmod +x telegram-cli
  xattr -d com.apple.quarantine telegram-cli
  ```
  Damit wird die macOS-Downloadsperre aufgehoben und die Datei ausführbar gemacht.
- **Python-Variante:** Erfordert Python 3.11 oder neuer. Prüfen Sie die Version mit `python3 --version`. Falls nötig, installieren Sie Python von <https://www.python.org/downloads/>.

### Schritt 2 — Telegram-Anwendung erstellen

Um telegram-cli zu verwenden, benötigen Sie eigene Telegram-API-Zugangsdaten. Dies ist eine einmalige Einrichtung — Sie müssen sie nie wiederholen.

1. Öffnen Sie <https://my.telegram.org/apps> in einem Browser und melden Sie sich mit Ihrer Telegram-Telefonnummer an.
2. Klicken Sie auf **API development tools**.
3. Füllen Sie das Formular **Create new application** aus. App-Titel und Kurzname können beliebig sein, z. B. `synchromessotron` / `syncbot`. Als Plattform kann `Other` stehen bleiben.

   ![Dialogfeld „Neue Anwendung erstellen"](../docs/images/telegram1.png)

4. Klicken Sie auf **Create application**.
5. Sie sehen Ihre **App api_id** (eine kurze Zahl) und **App api_hash** (eine lange Zeichenkette aus Buchstaben und Ziffern). Lassen Sie diesen Browser-Tab geöffnet — Sie benötigen beide Werte im nächsten Schritt.

   ![api_id und api_hash](../docs/images/telegram2.png)

### Eingabeaufforderung öffnen (Windows) oder Terminal (macOS)

Sie benötigen ein Eingabeaufforderungs-Fenster (Windows) oder ein Terminal-Fenster (macOS), das im Ordner geöffnet ist, in dem Sie die telegram-cli-Datei gespeichert haben.

> **Windows — Eingabeaufforderung im Ordner öffnen:**
>
> 1. Öffnen Sie den **Datei-Explorer** und navigieren Sie zum Ordner, in dem Sie `telegram-cli.exe` gespeichert haben.
> 2. Klicken Sie auf die Adressleiste oben (sie zeigt den Ordnerpfad an).
> 3. Tippen Sie `cmd` und drücken Sie **Enter**. Ein schwarzes Eingabeaufforderungsfenster öffnet sich direkt in diesem Ordner.

> **macOS — Terminal im Ordner öffnen:**
>
> 1. Öffnen Sie den **Finder** und navigieren Sie zum Ordner, in dem Sie `telegram-cli` gespeichert haben.
> 2. Klicken Sie mit der rechten Maustaste (oder Control-Klick) auf den Ordner.
> 3. Wählen Sie **Neues Terminal beim Ordner**. Ein Terminal-Fenster öffnet sich in diesem Ordner.
>
> (Falls Sie diese Option nicht sehen: gehen Sie zu **Systemeinstellungen → Datenschutz & Sicherheit → Erweiterungen → Finder-Erweiterungen** und aktivieren Sie **Neues Terminal beim Ordner**.)

### Schritt 3 — Sitzung einrichten

Öffnen Sie die Eingabeaufforderung (Windows) oder das Terminal (macOS) im Ordner, in dem Sie die Datei abgelegt haben (siehe oben), und führen Sie aus:

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli init` |
| **macOS** | `./telegram-cli init` |
| **Python** | `python3 telegram-cli.pyz init` |

Der Befehl wird:
1. Nach Ihrer **api_id**, Ihrem **api_hash** und Ihrer **Telefonnummer** fragen (aus Schritt 2).
2. Einen Anmeldecode an Ihre Telegram-App senden — geben Sie ihn ein, wenn Sie dazu aufgefordert werden.
3. Falls Sie die Zwei-Schritt-Verifizierung aktiviert haben, nach Ihrem **2FA-Passwort** fragen.
4. Eine `config.yaml`-Datei mit Ihren Zugangsdaten und der Sitzung erstellen.

> **Was ist das 2FA-Passwort?** Es ist ein Passwort, das *Sie selbst festgelegt haben*, als Sie die Zwei-Schritt-Verifizierung in Telegram aktiviert haben. Zum Prüfen oder Ändern: Telegram öffnen → **Einstellungen → Datenschutz und Sicherheit → Zwei-Schritt-Verifizierung**.

**Erwartetes Ergebnis:**

```
✓ Session created and saved to config.yaml
  Run 'telegram-cli whoami' to verify.
```

### Schritt 4 — Einrichtung überprüfen

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Erwartetes Ergebnis:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Falls stattdessen ein Fehler angezeigt wird, lesen Sie den Abschnitt [Fehlerbehandlung](#fehlerbehandlung) weiter unten.

Überprüfen Sie außerdem, ob Telegram erreichbar ist:

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli ping` |
| **macOS** | `./telegram-cli ping` |
| **Python** | `python3 telegram-cli.pyz ping` |

**Erwartetes Ergebnis:**

```
✓ Telegram is reachable (42.3 ms)
```

---

## Sicherheit — Zugangsdaten schützen

Die `config.yaml`-Datei, die telegram-cli erstellt, enthält Ihre Telegram-API-Zugangsdaten und Ihre Anmeldesitzung. **Jede Person, die diese Datei hat, kann auf Ihr Telegram-Konto zugreifen.**

**Regeln:**

1. **Teilen Sie `config.yaml` niemals mit jemandem.** Behandeln Sie sie wie ein Passwort.
2. **Laden Sie sie niemals ins Internet hoch** — legen Sie sie nicht auf GitHub, Google Drive, Dropbox, in E-Mails oder an einem gemeinsam genutzten Ort ab.
3. **Bewahren Sie sie nur im selben Ordner wie die telegram-cli-Datei** auf Ihrem eigenen Computer auf.
4. **Falls Sie vermuten, dass jemand Ihre `config.yaml` gesehen hat** — widerrufen Sie die Sitzung sofort in Telegram: gehen Sie zu **Einstellungen → Geräte** (oder **Einstellungen → Datenschutz und Sicherheit → Aktive Sitzungen**) und beenden Sie die verdächtige Sitzung. Führen Sie dann erneut `telegram-cli init` aus, um eine neue zu erstellen.

> Die Datei `config.yaml.example` ist eine Vorlage ohne echte Zugangsdaten — sie kann bedenkenlos geteilt werden.

---

## Speicherort der Dateien

Alle von telegram-cli erzeugten Daten (Sicherungen, heruntergeladene Medien) werden in einem **Ausgabeordner** gespeichert.

### Standardspeicherort

Standardmäßig wird ein Ordner namens `synchromessotron` in dem Ordner erstellt, aus dem Sie telegram-cli ausführen:

```
<aktueller Ordner>/synchromessotron/
```

### Anderen Ordner wählen

Sie können mit `--outdir` einen anderen Speicherort wählen:

| Plattform | Beispiel |
|-----------|---------|
| **Windows** | `telegram-cli backup -1001234567890 --outdir=C:\MyBackups` |
| **macOS** | `./telegram-cli backup -1001234567890 --outdir=/Users/yourname/MyBackups` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --outdir=/path/to/my/data` |

> **Konfliktregelung:** Wenn sowohl `--outdir` als auch `output_dir` in `config.yaml` gesetzt sind und auf unterschiedliche Pfade verweisen, wird der Befehl mit einem Fehler beendet. Entfernen Sie einen der Einträge, um den Konflikt zu lösen.

telegram-cli prüft vor dem Start, ob in den Ordner geschrieben werden kann. Die meisten Speicherorte auf Ihrem Desktop oder in Ihrem Benutzerverzeichnis haben bereits Schreibberechtigung. Falls Sie einen Fehler bezüglich der Schreibberechtigung erhalten, lesen Sie den Abschnitt [Fehlerbehebung](#fehlerbehebung).

### Ordnerstruktur für Gespräche

Für jedes Gespräch wird ein Unterordner nach folgendem Benennungsschema erstellt:

```
<erste 10 Zeichen des Namens>_<Gesprächs-ID>
```

- Leerzeichen im Namen werden durch Unterstriche (`_`) ersetzt.
- Ist der Name kürzer als 10 Zeichen, wird der vollständige Name verwendet.

| Gespräch | Unterordner |
|----------|-------------|
| `Мемуары кочевого программиста. Байки, были, думы` (ID -718738386) | `Мемуары_ко_718738386` |
| `Telegram` (ID 777000) | `Telegram_777000` |

Innerhalb jedes Gesprächsordners werden Nachrichten nach Jahr geordnet, und dann nach Monat oder Tag, wenn es viele Nachrichten gibt (siehe [Erweiterte Funktionen](#erweiterte-funktionen) für Details).

### Welche Dateien gespeichert werden

Auf jeder Ebene werden zwei Dateien erstellt:

| Datei | Inhalt |
|-------|--------|
| `messages.json` | Vollständige Nachrichtendaten (zur Verwendung mit anderen Werkzeugen). |
| `messages.md` | Autor, Datum und Nachrichtentext — leicht lesbar in jedem Texteditor. |

### Fotos, Videos und andere Inhalte speichern

Standardmäßig werden nur Nachrichten gespeichert. Um weitere Inhalte einzuschließen, fügen Sie dem Befehl `backup` Flags hinzu:

| Flag | Was gespeichert wird |
|------|----------------------|
| `--media` | Fotos und Videos |
| `--files` | Dokumente und Dateianhänge |
| `--music` | Audiodateien |
| `--voice` | Sprachnachrichten |
| `--links` | Link-Vorschauen und URLs |
| `--gifs` | GIF-Animationen |
| `--members` | Liste der Gesprächsteilnehmer |

Beispiel — Nachrichten und Fotos sichern:

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli backup -1001234567890 --media` |
| **macOS** | `./telegram-cli backup -1001234567890 --media` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --media` |

Beispiel — alles sichern:

```
telegram-cli backup -1001234567890 --media --files --music --voice --links --gifs --members
```

### Beispiel-Ordnerstruktur

Nach dem Ausführen von `backup` mit `--media --members`:

```
synchromessotron/
├── Мемуары_ко_718738386/
│   ├── members/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── messages.json
│   │   │   ├── messages.md
│   │   │   └── media/
│   │   └── 02/
│   │       ├── messages.json
│   │       └── messages.md
│   └── 2026/
│       ├── messages.json
│       └── messages.md
└── Telegram_777000/
    └── 2026/
        ├── messages.json
        └── messages.md
```

In diesem Beispiel:
- „Мемуары кочевого…" hatte im Jahr 2025 mehr als 50 Nachrichten, daher wurde es in monatliche Unterordner aufgeteilt. Im Jahr 2026 gab es weniger Nachrichten, sodass sie im Jahresordner zusammenbleiben.
- „Telegram" hatte insgesamt wenige Nachrichten — keine monatliche Aufteilung erforderlich.

---

## Befehlsreferenz

### get-dialogs — Gespräche auflisten

```
get-dialogs [--limit=N] [--outdir=DIR]
```

**Parameter:**

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `--limit` | 100 | Maximale Anzahl der zurückgegebenen Gespräche. Verwenden Sie `--limit=500` oder höher für mehr Ergebnisse. |
| `--outdir` | — | Speichert außerdem `dialogs.json` in diesen Ordner (siehe [Speicherort der Dateien](#speicherort-der-dateien)). |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli get-dialogs --limit=50` |
| **macOS** | `./telegram-cli get-dialogs --limit=50` |
| **Python** | `python3 telegram-cli.pyz get-dialogs --limit=50` |

**Erwartetes Ergebnis:**

```
  TYPE         ID                 NAME
  ------------ ------------------ ------------------------------------------
  User         123456789          Your Name  @yourhandle
  Channel      -1001234567890     Family Group  @familygroup
  Chat         -987654321         Old Project

3 dialogs found.
```

Mit `--outdir` wird die Tabelle weiterhin auf dem Bildschirm ausgegeben und `dialogs.json` wird zusätzlich im Ausgabeordner gespeichert.

Bei Fehlern: `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`, `SESSION_INVALID`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### backup — Nachrichten sichern

```
backup <dialog_id> [--since=TIMESTAMP] [--upto=TIMESTAMP] [--limit=N] [--outdir=DIR]
       [--media] [--files] [--music] [--voice] [--links] [--gifs] [--members]
       [--estimate] [--count]
```

**Parameter:**

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `<dialog_id>` | — | Gesprächs-ID (erforderlich). Verwenden Sie `get-dialogs`, um sie zu finden. |
| `--since` | — | Nur Nachrichten herunterladen, die **nach** diesem Datum und dieser Uhrzeit gesendet wurden (Format: `2026-01-01T00:00:00+00:00`). |
| `--upto` | — | Nur Nachrichten herunterladen, die **bis einschließlich** diesem Datum und dieser Uhrzeit gesendet wurden. |
| `--limit` | 100 | Maximale Anzahl der herunterzuladenden Nachrichten. |
| `--outdir` | `./synchromessotron` | Dateien in diesen Ordner statt in den Standardordner speichern. |
| `--media` | aus | Fotos und Videos ebenfalls herunterladen. |
| `--files` | aus | Dokumente und Dateianhänge ebenfalls herunterladen. |
| `--music` | aus | Audiodateien ebenfalls herunterladen. |
| `--voice` | aus | Sprachnachrichten ebenfalls herunterladen. |
| `--links` | aus | Link-Vorschauen und URLs ebenfalls speichern. |
| `--gifs` | aus | GIF-Animationen ebenfalls herunterladen. |
| `--members` | aus | Liste der Gesprächsteilnehmer ebenfalls speichern. |
| `--estimate` | aus | Zeigt die geschätzte Dauer der Sicherung an und beendet den Vorgang. Es wird nichts heruntergeladen. |
| `--count` | aus | Zeigt die Anzahl der vorhandenen Nachrichten und Dateien an und beendet den Vorgang. Es wird nichts heruntergeladen. |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli backup -1001234567890 --limit=500` |
| **macOS** | `./telegram-cli backup -1001234567890 --limit=500` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --limit=500` |

**Erwartetes Ergebnis** (nur Nachrichten):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
```

**Erwartetes Ergebnis** (mit `--media --files`):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
✓ 23 media files downloaded
✓ 7 documents downloaded
```

**Inkrementelle Sicherung** — nur Nachrichten ab einem bestimmten Datum:

```
telegram-cli backup -1001234567890 --since=2026-03-01
```

**Erwartetes Ergebnis:**

```
✓ 12 messages saved to synchromessotron/Telegram_777000/2026/03/
```

**Zeitfenster** — Nachrichten zwischen zwei Datumsangaben (`--since` muss früher sein als `--upto`):

```
telegram-cli backup -1001234567890 ^
    --since=2026-01-01T00 ^
    --upto=2026-01-01T10
```

> **Häufiger Fehler:** Wenn `--since` auf ein Datum *nach* `--upto` gesetzt wird, werden 0 Nachrichten gespeichert, da keine Nachricht gleichzeitig nach Februar und vor Januar liegen kann. Überprüfen Sie immer, dass `--since` ein früheres Datum als `--upto` ist.

**Zeitschätzung vor einer großen Sicherung:**

```
telegram-cli backup -1001234567890 --limit=5000 --estimate
```

**Erwartetes Ergebnis:**

```
≈ 12 minutes (5000 messages, estimated 2.4 ms per message)
```

Die Schätzung ist ungefähr — die tatsächliche Dauer hängt von Ihrer Internetverbindung und den Telegram-Limits ab. Es wird nichts heruntergeladen.

**Nachrichten zählen vor dem Herunterladen:**

```
telegram-cli backup -1001234567890 --count
```

**Erwartetes Ergebnis:**

```
Messages: 350 total
  photo: 42
  link/webpage: 8
  video: 5
  file/document: 2
```

Bei Fehlern: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### send — Nachricht senden

```
send <dialog_id> --text=TEXT
```

**Parameter:**

| Parameter | Beschreibung |
|-----------|--------------|
| `<dialog_id>` | Gesprächs-ID (erforderlich). |
| `--text` | Der zu sendende Text (erforderlich). |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **macOS** | `./telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **Python** | `python3 telegram-cli.pyz send -1001234567890 --text="Hello from CLI!"` |

**Erwartetes Ergebnis:**

```
✓ Message sent
  ID:    12345
  Date:  2026-03-16 14:30:00
  Text:  Hello from CLI!
```

Bei Fehlern: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`, `RATE_LIMITED`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### edit — Nachricht bearbeiten

```
edit <dialog_id> <message_id> --text=TEXT
```

**Parameter:**

| Parameter | Beschreibung |
|-----------|--------------|
| `<dialog_id>` | Gesprächs-ID (erforderlich). |
| `<message_id>` | Nachrichten-ID (erforderlich). |
| `--text` | Neuer Nachrichtentext (erforderlich). |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **macOS** | `./telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **Python** | `python3 telegram-cli.pyz edit -1001234567890 42 --text="Corrected text"` |

**Erwartetes Ergebnis:**

```
✓ Message edited
  ID:    42
  Date:  2026-03-16 14:30:00
  Text:  Corrected text
```

Bei Fehlern: `ENTITY_NOT_FOUND`, `NOT_MODIFIED`, `PERMISSION_DENIED`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### delete — Nachrichten löschen

```
delete <dialog_id> <message_id> [<message_id> ...]
```

**Parameter:**

| Parameter | Beschreibung |
|-----------|--------------|
| `<dialog_id>` | Gesprächs-ID (erforderlich). |
| `<message_id>` | Eine oder mehrere Nachrichten-IDs (erforderlich). |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli delete -1001234567890 42 43 44` |
| **macOS** | `./telegram-cli delete -1001234567890 42 43 44` |
| **Python** | `python3 telegram-cli.pyz delete -1001234567890 42 43 44` |

**Erwartetes Ergebnis:**

```
✓ 3 messages deleted
```

Bei Fehlern: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### download-media — Foto, Video oder Datei herunterladen

```
download-media <dialog_id> <message_id> [--outdir=DIR]
```

**Parameter:**

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `<dialog_id>` | — | Gesprächs-ID (erforderlich). |
| `<message_id>` | — | Nachrichten-ID (erforderlich). |
| `--outdir` | `./synchromessotron` | In diesen Ordner statt in den Standardordner speichern. |

Die Datei wird im entsprechenden Unterordner (`media/`, `files/`, `music/`, `voice/`, `gifs/`) innerhalb des Gesprächsordners gespeichert.

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli download-media -1001234567890 42` |
| **macOS** | `./telegram-cli download-media -1001234567890 42` |
| **Python** | `python3 telegram-cli.pyz download-media -1001234567890 42` |

**Erwartetes Ergebnis:**

```
✓ Downloaded: synchromessotron/Telegram_777000/2026/03/media/photo_42.jpg (2.1 MB)
```

Bei Fehlern: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### ping — Telegram-Erreichbarkeit prüfen

```
ping
```

Keine Parameter.

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli ping` |
| **macOS** | `./telegram-cli ping` |
| **Python** | `python3 telegram-cli.pyz ping` |

**Erwartetes Ergebnis:**

```
✓ Telegram is reachable (42.3 ms)
```

Bei Fehlern: `NETWORK_ERROR`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### whoami — Anmeldung prüfen

```
whoami
```

Keine Parameter.

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Erwartetes Ergebnis:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Bei Fehlern: `AUTH_FAILED`, `SESSION_INVALID`. Siehe [Fehlerbehandlung](#fehlerbehandlung).

---

### help — Hilfe in Ihrer Sprache anzeigen

```
help [LANG] [COMMAND]
```

**Parameter:**

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `LANG` | `en` | Sprachcode. Unterstützt: `en`, `ru`, `fa`, `tr`, `ar`, `de`. |
| `COMMAND` | — | Falls angegeben, wird nur die Hilfe für diesen Befehl angezeigt. |

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli help de backup` |
| **macOS** | `./telegram-cli help de backup` |
| **Python** | `python3 telegram-cli.pyz help de backup` |

**Erwartetes Ergebnis** (allgemein, Englisch):

```
telegram-cli — command-line tool for Telegram

Commands:
  init            Set up credentials and session
  whoami          Validate session and show user info
  ping            Check Telegram availability
  get-dialogs     List your dialogs
  backup          Full or incremental message backup
  send            Send a message
  edit            Edit a previously sent message
  delete          Delete own messages
  download-media  Download media from a message
  help            Show this help
  version         Show version information

Run 'telegram-cli help <lang> <command>' for details.
```

---

### version — Versionsinformationen anzeigen

```
version
```

Keine Parameter.

**Beispiele:**

| Plattform | Befehl |
|-----------|--------|
| **Windows** | `telegram-cli version` |
| **macOS** | `./telegram-cli version` |
| **Python** | `python3 telegram-cli.pyz version` |

**Erwartetes Ergebnis:**

```json
{
  "cli": { "version": "1.0.0", "build": 1, "datetime": "2026-03-17T00:00:00Z" },
  "lib": { "version": "1.2.0", "build": 3, "datetime": "2026-03-18T00:00:00Z" }
}
```

---

## Fehlerbehandlung

Wenn etwas schiefgeht, gibt telegram-cli eine Meldung aus, die das Problem und mögliche Lösungsschritte beschreibt.

Beispiel:

```
Error [RATE_LIMITED]: Too many requests — retry after 30s
  retry_after: 30
```

**Bedeutung der einzelnen Fehler und empfohlene Maßnahmen:**

| Fehler | Was ist passiert | Was tun |
|--------|-----------------|---------|
| `AUTH_FAILED` | Ihr Telegram-Konto wurde deaktiviert oder gesperrt. | Wenden Sie sich an den Telegram-Support. |
| `ENTITY_NOT_FOUND` | Die verwendete Gesprächs- oder Nachrichten-ID existiert nicht. | Verwenden Sie `get-dialogs`, um die richtige ID zu finden. |
| `INTERNAL_ERROR` | Ein unerwarteter Fehler ist innerhalb von telegram-cli aufgetreten. | Melden Sie das Problem und fügen Sie die vollständige Fehlermeldung bei. |
| `NETWORK_ERROR` | telegram-cli kann Telegram nicht erreichen. | Überprüfen Sie Ihre Internetverbindung oder versuchen Sie es später erneut. |
| `NOT_MODIFIED` | Sie haben versucht, eine Nachricht zu bearbeiten, aber der neue Text ist identisch mit dem alten. | Verwenden Sie einen anderen Text. |
| `PERMISSION_DENIED` | Sie haben keine Berechtigung, aus diesem Gespräch zu lesen oder darin zu schreiben. | Überprüfen Sie Ihre Zugriffsrechte für dieses Gespräch. |
| `RATE_LIMITED` | Sie haben in kurzer Zeit zu viele Anfragen gesendet; Telegram bittet Sie zu warten. | Warten Sie die in der Fehlermeldung angegebene Anzahl von Sekunden und versuchen Sie es dann erneut. |
| `SESSION_INVALID` | Ihre Anmeldesitzung ist abgelaufen oder wurde widerrufen. | Führen Sie `telegram-cli init` erneut aus, um sich wieder anzumelden. |

## Rückgabecodes

Wenn telegram-cli beendet wird, gibt es eine Zahl an das Betriebssystem zurück (nützlich für Skripte):

| Code | Bedeutung |
|------|-----------|
| 0 | Alles hat funktioniert. |
| 1 | Sie haben einen falschen Befehl oder Parameter verwendet. |
| 2 | Ein Telegram-Fehler ist aufgetreten (siehe Tabelle oben). |

---

## Erweiterte Funktionen

### Ordnertiefe mit `--split_threshold` steuern

Standardmäßig werden Nachrichten in Jahresordner gruppiert. Enthält ein Jahr viele Nachrichten, erstellt telegram-cli automatisch monatliche Unterordner darin, dann tägliche, stündliche und schließlich minutengenaue Unterordner, wenn nötig.

Der Schwellenwert, ab dem eine tiefere Unterteilung ausgelöst wird, wird durch `--split_threshold` gesteuert (Standard: `100`). Wenn Sie beispielsweise eine Sicherung mit `--split_threshold=20` ausführen, wird eine neue Unterordnerebene erstellt, sobald ein Ordner mehr als 20 Nachrichten enthalten würde.

```
telegram-cli backup -1001234567890 --split_threshold=20
```

Dies ist nützlich, wenn Sie eine feingranularere Strukturierung für sehr aktive Gespräche wünschen. Für die meisten Nutzer ist der Standardwert ausreichend.

Die Tiefe folgt dieser Reihenfolge:

```
year/ → month/ → day/ → hour/ → minute/
```

Nachrichten werden immer auf der tiefsten Ebene gespeichert — niemals aufgeteilt auf zwei Ebenen.

---

## Fehlerbehebung

### telegram-cli kann Telegram nicht erreichen

Wenn `NETWORK_ERROR` angezeigt wird, ist Telegram von Ihrem Computer aus nicht erreichbar.

**Versuchen Sie diese Schritte in der angegebenen Reihenfolge:**

1. Überprüfen Sie, ob Ihre Internetverbindung funktioniert (öffnen Sie eine Website im Browser).
2. Versuchen Sie es einige Minuten später erneut — Telegram könnte vorübergehend nicht verfügbar sein.
3. Falls Telegram in Ihrer Region gesperrt ist, erwägen Sie die Verwendung eines VPN.
4. Führen Sie `telegram-cli ping` aus, um zu bestätigen, ob das Problem an der Verbindung oder an Ihrer Sitzung liegt.

---

### Fehler bei der Schreibberechtigung

Wenn telegram-cli meldet, dass nicht in den Ausgabeordner geschrieben werden kann, verfügt Ihr Benutzerkonto nicht über die Berechtigung, dort Dateien zu erstellen.

**Einfachste Lösung für die meisten Nutzer:** Führen Sie telegram-cli aus Ihrem Benutzerverzeichnis oder Desktop aus, oder verwenden Sie `--outdir`, um auf einen Ordner in Ihrem Benutzerverzeichnis zu verweisen. Diese Speicherorte haben immer Schreibberechtigung.

**Windows — Schreibberechtigung prüfen und erteilen:**

Klicken Sie mit der rechten Maustaste auf den Zielordner → **Eigenschaften** → Registerkarte **Sicherheit** → prüfen Sie, ob Ihr Benutzer die Berechtigung **Schreiben** hat. Falls nicht, klicken Sie auf **Bearbeiten**, wählen Sie Ihren Benutzer aus und aktivieren Sie das Kontrollkästchen **Schreiben**.

Für erfahrene Nutzer kann dasselbe in der Eingabeaufforderung durchgeführt werden:

```
icacls "C:\path\to\folder"
```

Suchen Sie nach `(W)` oder `(F)` neben Ihrem Benutzernamen. Um Schreibberechtigung zu erteilen:

```
icacls "C:\path\to\folder" /grant %USERNAME%:W
```

**macOS / Linux — Schreibberechtigung prüfen und erteilen:**

Die meisten Ordner in Ihrem Benutzerverzeichnis (Desktop, Dokumente, Downloads) haben bereits Schreibberechtigung. Wenn Sie einen benutzerdefinierten Pfad verwenden, prüfen Sie diesen mit:

```
ls -ld /path/to/folder
```

Falls `w` in den Berechtigungen fehlt, erteilen Sie sie mit:

```
chmod u+w /path/to/folder
```

---

### Anmeldecode kommt nicht an

Falls Sie nach dem Ausführen von `telegram-cli init` keinen Anmeldecode erhalten haben:

1. Stellen Sie sicher, dass die eingegebene Telefonnummer korrekt ist und die Landesvorwahl enthält (z. B. `+4915123456789`).
2. Überprüfen Sie Ihre Telegram-App — der Code kommt als reguläre Telegram-Nachricht vom offiziellen Telegram-Konto an.
3. Warten Sie eine Minute und führen Sie `telegram-cli init` erneut aus.

---

### Sitzung abgelaufen

Wenn `SESSION_INVALID` angezeigt wird, ist Ihre Anmeldung abgelaufen oder wurde widerrufen (zum Beispiel, wenn Sie alle aktiven Sitzungen in den Telegram-Einstellungen beendet haben).

Führen Sie `telegram-cli init` aus, um sich erneut anzumelden.
