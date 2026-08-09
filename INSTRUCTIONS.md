# Burghley Scan (lite) - Install & Run Instructions

This file is meant to travel with `burghley-scan.exe`. If you've downloaded
just the executable from a GitHub release, this is everything you need.

## What this tool does

Scans a Git repository for patterns that correlate with AI-generated code
shipping without review: large commits with no test changes, untested
files, AI-flavoured commit messages, hallucinated dependencies, oversized
files, and generic naming density.

It prints simple category counts to your screen. Nothing is written to
disk, and nothing is uploaded anywhere. Full stop.

It does **not** scan for secrets (API keys, passwords, connection
strings). That check only exists in the paid audit - see below.

## Before you begin

1. **The folder must be a Git repository.** The tool reads git history
   (`git log`, `git ls-files`) to find recent activity. Without a `.git`
   folder, it will exit with an error.
2. **Git must be on your machine and on your PATH.** Same commands as
   above - all local, nothing touches a remote.
3. **Windows.** This build is a Windows executable. If you're on macOS or
   Linux, run it from source instead (see the main [README](README.md)).

## How to run it

Open Command Prompt or PowerShell.

**Option A** - drop `burghley-scan.exe` inside the repo you want to scan,
then run:

```
burghley-scan.exe
```

**Option B** - from anywhere, point it at the repo:

```
burghley-scan.exe C:\path\to\your\repo
```

It finishes in under a minute for most repos.

## What you'll see

```
Scanned 72 files touched across 25 commits over the last 30 days
Large commits with no test changes: 12
Untested files: 72
Possible AI-usage signals: 17
Oversized files: 2
Generic naming density: 7

These are correlation signals, not proof. See the README for how to read them.
Nothing was uploaded or written to disk. This scan ran entirely on your machine.
```

That's the whole output. No file paths, line numbers, commit hashes, or
names - just counts, so you can see whether there's a pattern worth
looking into without anything leaving your machine.

## "Windows protected your PC" warning

This executable isn't code-signed yet, so Windows SmartScreen may show an
"unrecognised publisher" warning the first time you run it. This is
expected for new, unsigned software - click **More info**, then
**Run anyway**. The tool makes zero network connections and writes
nothing to disk; there's nothing here to phone home or persist.

## No network connections

This tool makes zero network calls, checked and verified before release.
It reads local files and runs local Git commands only. Run it on a
machine with no internet access and it will complete without complaint.

## Licence

Licensed under the Burghley Business Source License (see
[LICENCE.md](LICENCE.md)). In short: you can inspect, run, and fork this
tool. You cannot sell it or use it to build a competing product.

## Want the full picture?

This free tool tells you there's a pattern. The full audit tells you why,
with detailed findings, plain-language manager reports, technical
breakdowns, and team training recommendations - still without your code
ever leaving your machine.

[Burghley AI Services](https://burghley-ai-services.co.uk) - [info@burghley-ai-services.co.uk](mailto:info@burghley-ai-services.co.uk)
