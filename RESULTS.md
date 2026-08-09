# Understanding your scan results

Burghley Scan (lite) prints five numbers. This page explains what each one
actually counts, and what it does and doesn't tell you. All of them are
**correlation signals, not proof** - a high count means "worth a closer
look," not "AI definitely did this, unreviewed."

Every check below only looks at commits and files from the scan window
(the last 30 days, or the last 25-50 commits if the repo's too quiet for
30 days to say much) - not the whole repository history.

## Large commits with no test changes

**What it counts:** commits that changed 3 or more production files
(excluding vendored/third-party code) without touching a single test
file.

**Why it matters:** this is the strongest single signal the free tool
has for "shipped without proper review." A big change with no test
activity nearby is exactly the pattern that started this whole business
- a colleague's single-pass AI upgrade that nobody checked, including
the person who ran it.

**Reasons this can be high without AI being involved:**
- A team that tests manually instead of writing automated tests.
- Tests that live in a separate repository the scan can't see.
- A genuinely test-light project (early-stage, prototype, internal tool).

## Untested files

**What it counts:** files touched in the scan window that have no
matching test file anywhere in the repo, by filename convention
(`Foo.test.ts`, `test_foo.py`, `FooTests.cs`, and similar patterns),
excluding generated/designer files that nobody hand-writes tests for.

**Why it matters:** it's a snapshot of testing coverage for whatever's
actively being worked on right now, not the whole codebase. A file can
be old and stable and still show up here if it was touched recently.

**Reasons this can be high without AI being involved:** same as above -
manual testing, external test suites, or a project that simply doesn't
test much.

## Possible AI-usage signals

**What it counts:** this one number rolls up five separate checks, on
purpose - the free tool doesn't break these apart individually:

- **Co-authored-by trailers** naming an AI tool (Claude, Copilot,
  ChatGPT, Gemini, Cursor, etc.) in a commit message.
- **"Generated with/by" footers** referencing an AI tool.
- **Generic commit messages** - subjects like "fix bug", "update code",
  "improve performance" that carry no real information about what
  changed.
- **Boilerplate comments** - comments that just restate the next line of
  code (`// increment the counter`, `# initialize the variable`), a
  pattern common in AI-generated code that nobody edited afterwards.
- **Hallucinated dependencies** - imports that reference a package not
  declared in `package.json` or `requirements.txt`. This is a real
  build-integrity issue on its own (an undeclared import can break the
  build or pull an unpinned version), and separately correlates with
  "slopsquatting" - AI tools suggesting packages that don't actually
  exist.

**Why it matters:** none of these five prove AI was used, and none of
them prove a human didn't review the result either. They're worded as
"possible" throughout for that reason. What they're good at is spotting
the *absence* of review - a co-authored trailer or a generic commit
message costs nothing to add whether or not anyone checked the change
first.

**Reasons this can be high without being a problem:** teams that openly
and deliberately use AI tools with proper review will still trip the
co-authored-by and footer checks - disclosure isn't the issue, lack of
review is. The full audit looks at these signals alongside testing and
review evidence together, rather than counting them in isolation.

## Oversized files

**What it counts:** files over 500 lines, touched in the scan window.

**Why it matters:** large single-pass AI changes tend to produce large
files - functionality gets bolted on rather than extracted, because
nobody was reviewing structure as it grew. It's also just a general
maintainability smell independent of AI.

## Generic naming density

**What it counts:** files where more than 5% of lines contain a generic
identifier - `temp`, `tmp`, `data`, `value`, `result` - used as a
variable name.

**Why it matters:** heavy use of placeholder-style names is common in
fast, unreviewed code, AI-generated or not, where nobody went back to
give things meaningful names.

## What this tool deliberately leaves out

- **No secrets detection.** If this scan found an exposed API key or
  password and only told you about it via a paid report, that would be
  withholding a known active security risk for commercial leverage.
  It's simply not checked for in this tool, full stop.
- **No file paths, line numbers, commit hashes, author names, or
  dates.** You get counts, not a map of exactly what to look at. That's
  the difference between the free and paid tool.

## Want the detail behind these numbers?

This free tool tells you a pattern exists. It doesn't tell you which
6 commits, which 43 files, or who was involved - that's deliberate, not
a limitation we forgot to fix.

If any of these numbers look worth investigating, [**get in
touch**](https://burghley-ai-services.co.uk/contact) and we'll walk you
through the full audit: every finding broken down individually, a
plain-language report for managers, a technical report for developers,
and a best-practices plan with actual solutions - not just the list of
problems.

[Burghley AI Services](https://burghley-ai-services.co.uk) - [info@burghley-ai-services.co.uk](mailto:info@burghley-ai-services.co.uk)
