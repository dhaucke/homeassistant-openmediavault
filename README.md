![OpenMediaVault Integration für Home Assistant](https://raw.githubusercontent.com/dhaucke/homeassistant-openmediavault/master/assets/omv-banner.svg)

# OpenMediaVault

**Überwache dein OpenMediaVault-NAS in Home Assistant.**

[![Release](https://img.shields.io/github/v/release/dhaucke/homeassistant-openmediavault?style=flat-square)](https://github.com/dhaucke/homeassistant-openmediavault/releases/latest)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-18BCF2?style=flat-square)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/dhaucke/homeassistant-openmediavault?style=flat-square)](LICENSE)

**Dateisystem · System · Festplatten & S.M.A.R.T. · Dienste**

[Mit HACS installieren](https://my.home-assistant.io/redirect/hacs_repository/?owner=dhaucke&repository=homeassistant-openmediavault&category=integration) · [Problem melden](https://github.com/dhaucke/homeassistant-openmediavault/issues)

**Sprache:** [Deutsch](#deutsch) · [English](#english)

---

# Deutsch

## Warum dieser Fork existiert

Dies ist ein Fork von [tomaae/homeassistant-openmediavault](https://github.com/tomaae/homeassistant-openmediavault). Der letzte vom Maintainer selbst gemergte Beitrag liegt lange zurück; seitdem stapeln sich unbeantwortete Bugs — unter anderem [Issue #175](https://github.com/tomaae/homeassistant-openmediavault/issues/175) ("Lost connection can not connect again", offen seit 23. Juli 2026, mehrere Nutzer mit "same here", keine einzige Reaktion) und [Issue #169](https://github.com/tomaae/homeassistant-openmediavault/issues/169) ("Is this maintained or abandoned for good?", seit Oktober 2025 unbeantwortet).

Dieser Fork existiert, um genau solche Bugs tatsächlich anzugehen, statt auf eine Antwort zu warten, die nicht kommt.

## Was bisher gefixt wurde

- **Verbindungsfehler ohne echte Ursache (Issue #175):** `connect()` warf bei jedem Fehlschlag nur das generische `cannot_connect`, egal ob OMV tatsächlich unerreichbar war oder einfach nur eine Antwort schickte, die sich nicht als JSON parsen ließ (z. B. eine HTML-Fehlerseite). Die eigentliche Ursache wurde nirgends geloggt. Jetzt wird bei einem solchen Fehler der echte HTTP-Status und eine Vorschau der Antwort auf ERROR/WARNING-Level geloggt — sichtbar ohne Debug-Modus.
- **CI des Forks repariert:** mehrere kaputte/veraltete GitHub-Actions-Abhängigkeiten (u. a. ein hart von GitHub blockiertes `upload-artifact@v3`, eine Bandit-Sicherheitsprüfung, deren Docker-Image auf einem inzwischen archivierten Debian-Release aufbaute und nicht mehr baut) sowie ein fälschlich auf jeden Push statt nur auf Pull Requests feuernder Workflow.

## Was die Integration kann

- Dateisystem-Belegungs-Sensoren
- System-Sensoren (CPU, Arbeitsspeicher, Uptime)
- System-Status (verfügbare Updates, ausstehender Neustart, nicht übernommene Konfiguration)
- Festplatten- und S.M.A.R.T.-Sensoren
- Dienst-Sensoren

## Installation

### HACS (empfohlen)

1. In HACS das Drei-Punkte-Menü öffnen → **Custom repositories**.
2. `https://github.com/dhaucke/homeassistant-openmediavault` als Typ **Integration** hinzufügen.
3. **OpenMediaVault** installieren und Home Assistant neu starten.

### Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → OpenMediaVault**. Die Integration lässt sich mehrfach für verschiedene NAS-Geräte einrichten.

- **Name der Integration** — Anzeigename für dieses NAS
- **Host** — Hostname oder IP-Adresse
- **SSL verwenden** — Verbindung zu OMV per SSL
- **SSL-Zertifikat verifizieren** — Zertifikatsprüfung (benötigt ein vertrauenswürdiges Zertifikat)

## Debug-Logging aktivieren

Für detailliertere Logs (hilfreich beim Melden von Verbindungsproblemen) in der `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.openmediavault: debug
```

## Support

Dies ist ein kleiner, unbezahlter Fork, der gepflegt wird, um echte Bugs zu beheben, die im Original liegen bleiben — kein finanziertes oder im Team betreutes Projekt.

- [Issues](https://github.com/dhaucke/homeassistant-openmediavault/issues)

## Entwicklung

Es gibt kein Lokalise-Projekt für diesen Fork. Um eine Übersetzung hinzuzufügen oder zu korrigieren, die entsprechende Datei direkt bearbeiten und einen PR öffnen.

## Haftungsausschluss

Dieses Paket und sein Autor stehen in keiner Verbindung zu OpenMediaVault. Nutzung auf eigene Gefahr.

## Lizenz

Veröffentlicht unter der Apache-Lizenz 2.0, unverändert übernommen von [tomaae/homeassistant-openmediavault](https://github.com/tomaae/homeassistant-openmediavault) — siehe [LICENSE](LICENSE).

---

# English

## Why this fork exists

This is a fork of [tomaae/homeassistant-openmediavault](https://github.com/tomaae/homeassistant-openmediavault). It's been a long time since the maintainer merged anything themselves; since then, unanswered bugs have piled up — among them [issue #175](https://github.com/tomaae/homeassistant-openmediavault/issues/175) ("Lost connection can not connect again", open since July 23 2026, several users confirming "same here", zero response) and [issue #169](https://github.com/tomaae/homeassistant-openmediavault/issues/169) ("Is this maintained or abandoned for good?", unanswered since October 2025).

This fork exists to actually address bugs like these instead of waiting for a response that isn't coming.

## What's been fixed so far

- **Connection errors with no real cause surfaced (issue #175):** `connect()` only ever raised the generic `cannot_connect` on failure, regardless of whether OMV was genuinely unreachable or just sent back a response that couldn't be parsed as JSON (e.g. an HTML error page). The real cause was never logged anywhere. It now logs the actual HTTP status and a preview of the response at ERROR/WARNING level when this happens - visible without enabling debug logging.
- **Fixed this fork's own CI:** several broken/outdated GitHub Actions dependencies (including `upload-artifact@v3`, now hard-blocked by GitHub, and a Bandit security-check action whose Docker image was built from an EOL'd Debian release that no longer builds), plus a workflow that incorrectly triggered on every push instead of only pull requests.

## What this integration does

- Filesystem usage sensors
- System sensors (CPU, Memory, Uptime)
- System status sensors (available updates, pending reboot, dirty config)
- Disk and S.M.A.R.T. sensors
- Service sensors

## Installation

### HACS (preferred)

1. In HACS, open the three-dot menu → **Custom repositories**.
2. Add `https://github.com/dhaucke/homeassistant-openmediavault` as type **Integration**.
3. Install **OpenMediaVault** and restart Home Assistant.

### Setup

**Settings → Devices & services → Add integration → OpenMediaVault**. You can add this integration multiple times for different NAS devices.

- **Name of the integration** - friendly name for this NAS
- **Host** - hostname or IP address
- **Use SSL** - connect to OMV over SSL
- **Verify SSL certificate** - validate the certificate (needs a trusted certificate)

## Enabling debug logging

For more detailed logs (useful when reporting connection issues), add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.openmediavault: debug
```

## Support

This is a small, unpaid fork maintained to actually fix real bugs left unaddressed upstream - not a funded or team-maintained project.

- [Issues](https://github.com/dhaucke/homeassistant-openmediavault/issues)

## Development

There is no Lokalise project for this fork. To add or fix a translation, edit the relevant file directly and open a PR.

## Disclaimer

This package and its author are not affiliated with OpenMediaVault. Use at your own risk.

## License

Released under the Apache License 2.0, unchanged from [tomaae/homeassistant-openmediavault](https://github.com/tomaae/homeassistant-openmediavault) - see [LICENSE](LICENSE).
