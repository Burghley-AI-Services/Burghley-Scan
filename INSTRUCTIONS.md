# Burghley Scan - Install & Run Instructions

This file is meant to travel with `burghley-scan.exe`. If you've downloaded
just the executable from a GitHub release, this is everything you need.

## What this tool does

Scans a Git repository for patterns that correlate with AI-generated code
shipping without review: large commits with no test changes, untested
files, AI-flavoured commit messages, hallucinated dependencies, oversized
files, and generic naming density.

By default it opens a small dashboard window: pick the repository folder,
click **Run scan**, and the five category counts appear as cards with a
bar for each. Nothing is written to disk, and nothing is uploaded anywhere.
Full stop.

It does **not** scan for secrets (API keys, passwords, connection
strings). That check only exists in the paid audit - see below.

## Before you begin

1. **The folder must be a Git repository.** The tool reads git history
   (`git log`, `git ls-files`) to find recent activity. Without a `.git`
   folder, it will show an error.
2. **Git must be on your machine and on your PATH.** Same commands as
   above - all local, nothing touches a remote.
3. **Windows.** This build is a Windows executable, and the GUI needs the
   Microsoft Edge WebView2 runtime - already installed on most up-to-date
   Windows 10/11 machines. If it's missing, the tool automatically falls
   back to plain-text output instead of failing silently (see below). If
   you're on macOS or Linux, run it from source instead (see the main
   [README](README.md)).

## How to run it

Double-click `burghley-scan.exe`. That's it - the dashboard window opens
directly, no terminal needed. If you'd rather point it at a repository
that's not the one it's sitting in, use the **Select repository...**
button inside the window.

## Command-line mode

If you'd rather have plain-text output - for scripting, CI, or just
preference - open Command Prompt or PowerShell and run:

```
burghley-scan.exe --cli
```

or, pointing at a specific repo:

```
burghley-scan.exe --cli C:\path\to\your\repo
```

Example output:

```
Scanned 72 files touched across 25 commits over the last 30 days
Large commits with no test changes: 12
Untested files: 72
Possible AI-usage signals: 17
Oversized files: 2
Generic naming density: 7

These are correlation signals, not proof. See RESULTS.md for what each count means.
Nothing was uploaded or written to disk. This scan ran entirely on your machine.
```

No file paths, line numbers, commit hashes, or names in either mode - just
counts, so you can see whether there's a pattern worth looking into without
anything leaving your machine.

## "Windows protected your PC" warning

This executable isn't code-signed yet, so Windows SmartScreen may show an
"unrecognised publisher" warning the first time you run it. This is
expected for new, unsigned software - click **More info**, then
**Run anyway**. The tool makes zero network connections and writes
nothing to disk; there's nothing here to phone home or persist.

## No network connections

The scanning itself makes zero network calls, checked and verified before
release - it reads local files and runs local Git commands only, and will
complete without complaint on a machine with no internet access at all.

One honest caveat about the GUI: it's built on a library (pywebview) that's
*capable* of running a local web server as one of its supported modes. This
tool never uses that mode - the dashboard loads as a single self-contained
page, not a served file, so no server ever starts and no port ever opens.
If you want to verify that yourself rather than take our word for it, watch
for listening ports (e.g. `netstat`) while a scan runs, or just disconnect
your network entirely - either way, nothing will show up.

## Licence

Licensed under the Burghley Business Source License (see
[LICENCE.md](LICENCE.md)).

In short: you can inspect, run, and fork this tool. You cannot sell it or use it to build a competing product.

## Want the full picture?

This free tool tells you there's a pattern. The full audit tells you why,
with detailed findings, plain-language manager reports, technical
breakdowns, and team training recommendations - still without your code
ever leaving your machine.

[Burghley AI Services](https://burghley-ai-services.co.uk) - [info@burghley-ai-services.co.uk](mailto:info@burghley-ai-services.co.uk)
