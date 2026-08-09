# Burghley Scan
This is a free, open source, offline scanner that checks a codebase for unreviewed AI-assisted changes. This runs entirely on your own machine, nothing is ever uploaded.

## What it does
It looks through a codebase's git history for patterns that correlate with AI-generated code shipping without review:

- Large commits with no accompanying test changes.
- Files nobody's covered with tests.
- Commits that read like they were written by an AI (generic wording, boilerplate comments).
- Dependencies that don't exist (hallucinated packages).
- Oversized files and generic naming density.

It produces simple category counts, not full detail. Enough to see whether there's a real pattern worth looking into.

## Want the full picture?

This free tool shows you that there's a pattern. Our full audit will show you why there's a pattern, with:

- Detailed findings for every discovery, not just counts.
- Plain-language manager reports and technical breakdowns.
- Team coaching suggestions and best-practices recommendations.
- Everything delivered as branded PDFs, nothing uploaded from your machine

If this tool turns up something worth investigating, [**get in touch**](https://burghley-ai-services.co.uk/contact) and we'll walk you through a full audit process.

## Installation

### Requirements

- Python 3.7 or later
- Git (must be in your PATH)

### Setup

1. Download the latest executable from [**releases**](https://github.com/Burghley-AI-Services/burghley-scan/releases)
2. No installation needed - just run it

Or build from source:

```bash
git clone https://github.com/Burghley-AI-Services/burghley-scan.git
cd burghley-scan
pip install -r requirements.txt
python scan.py --help
```

## Usage

### GUI (default)

Run the executable (or `python scan.py` from source) and a window opens:
select the repository folder, click **Run scan**, and the results appear as
a dashboard - category cards with a bar for each count, not a wall of text.
Nothing is uploaded or sent anywhere; everything runs in that window, on
your machine.

### Command line (`--cli`)

For scripting, CI, or if you just prefer a terminal:

```bash
./burghley-scan --cli /path/to/your/repo
```

```
Scanned 340 files touched across 22 commits over the last 30 days
Large commits with no test changes: 6
Untested files: 43
Possible AI-usage signals: 8
Oversized files: 2
Generic naming density: 4
```

If the GUI can't start on your machine (for example, no WebView2 runtime -
see below), the tool automatically falls back to this same plain-text
output rather than failing silently.

### A note on the GUI and "no network calls"

The GUI is built on [pywebview](https://pywebview.flowrl.com/), which is
capable of running a local HTTP server as one of its supported modes. This
tool never uses that mode - the dashboard is loaded as a single self-contained
HTML string, not from a served file or URL, so no server ever starts and no
port ever opens. That means the old advice to "just grep the source for
`socket`/`requests`/`urllib`" no longer proves the whole story on its own,
since that capability now exists (unused) inside a dependency. If you want to
verify it yourself: run a scan with your network adapter disabled, or watch
for listening ports with `netstat` while it runs. Nothing will show up.

## What it does NOT do

- **It doesn't check for secrets.** This is intentional - if a real exposed credential exists, you should know about it immediately, not have it withheld behind a paywall.
- **It doesn't upload anything.** Every scan runs entirely offline on your machine. No internet connection required, no local server started either - see above.
- **It doesn't produce a detailed report.** For that, check out [Burghley AI Services](https://burghley-ai-services.co.uk) for a full audit.

## How to read the results

The counts are correlation signals, not proof. A high number of large commits with no tests could mean:

- AI-assisted development without proper review
- A team with weak testing discipline
- Legitimate work done in a separate test repository
- A project that relies on manual testing instead of automated tests

The tool flags the pattern. You decide what it means for your codebase.

For a breakdown of what each individual count means and what triggers it, see [RESULTS.md](RESULTS.md).

## Windows SmartScreen warning

When you first run this on Windows, you may see a "Windows protected your PC" prompt. This is normal for new, unsigned software. Click "More info" and then "Run anyway" to proceed. The tool makes no network calls and poses no risk to your system.

## Licence

This software is licensed under the Burghley Business Source License. See [LICENCE.md](LICENCE.md) for full terms.

In short: you can inspect, run, and fork this tool. You cannot sell it or use it to build a competing product.

## Contributions
Bug reports are welcome. If you find an issue, feel free to open up a [**GitHub issue**](https://github.com/Burghley-AI-Services/Burghley-Scan/issues/new) or [**email us**](mailto:info@burghley-ai-services.co.uk). 

This tool is already actively developed and managed by the Burghley AI Services team and as such PRs will not be accepted.

## Support

For questions or issues:
- Open an issue on GitHub
- Email [info@burghley-ai-services.co.uk](mailto:info@burghley-ai-services.co.uk)

## About Burghley AI Services

Burghley Scan is built by [Burghley AI Services](https://burghley-ai-services.co.uk), an independent audit service that checks codebases for ungoverned AI usage.

This free tool is the entry point. If you find patterns worth investigating, we offer a full audit with detailed findings, actionable reporting, and team training.
