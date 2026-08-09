"""
Builds the single self-contained HTML string for the GUI window.

Deliberately a single inline string, not separate .html/.css/.js files
loaded via url= - pywebview only starts its built-in local HTTP server
when a window is loaded from a local file/url. Loading from an inline
html= string never triggers that, so this stays true to the "zero
network calls, not even localhost" claim. See gui/app.py for the
pywebview wiring and the js_api bridge this page talks to.
"""

VERSION = "1.0.0-lite"

_STYLE = """
:root {
    color-scheme: dark;
    --bg: #0f1115;
    --panel: #171a21;
    --border: #262b36;
    --text: #e8e8ea;
    --muted: #9aa1b1;
    --accent: #4f8cff;
    --accent-dim: #2c3f66;
    --danger: #ff6b6b;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-user-select: none;
}
header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 24px;
    border-bottom: 1px solid var(--border);
}
header .brand { font-weight: 600; font-size: 16px; }
header .tagline { color: var(--muted); font-size: 13px; }
main { padding: 24px; max-width: 900px; margin: 0 auto; }

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
}

.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

button {
    font: inherit;
    background: var(--accent);
    color: #08101f;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
    cursor: pointer;
}
button:disabled { background: var(--accent-dim); color: var(--muted); cursor: not-allowed; }
button.secondary { background: transparent; border: 1px solid var(--border); color: var(--text); }

.path-label {
    font-family: Consolas, "Courier New", monospace;
    font-size: 13px;
    color: var(--muted);
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    flex: 1;
    min-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

#status { margin-top: 16px; color: var(--muted); font-size: 14px; }
#status.error { color: var(--danger); }

#results { display: none; margin-top: 24px; }
#results .meta { color: var(--muted); font-size: 13px; margin-bottom: 20px; }

.card {
    display: grid;
    grid-template-columns: 260px 1fr 48px;
    align-items: center;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
}
.card:last-child { border-bottom: none; }
.card .label { font-size: 14px; }
.card .label .desc { display: block; color: var(--muted); font-size: 12px; margin-top: 2px; }
.card .bar-track { background: var(--bg); border-radius: 4px; height: 10px; overflow: hidden; }
.card .bar-fill { background: var(--accent); height: 100%; border-radius: 4px; transition: width 0.4s ease; }
.card .count { text-align: right; font-weight: 700; font-size: 16px; }

#disclaimer {
    margin-top: 20px;
    font-size: 13px;
    color: var(--muted);
    line-height: 1.5;
}

#cta {
    margin-top: 24px;
    padding: 18px;
    border: 1px solid var(--accent-dim);
    border-radius: 8px;
    background: rgba(79, 140, 255, 0.08);
    font-size: 14px;
    line-height: 1.5;
}
#cta a { color: var(--accent); }

.spinner {
    width: 16px; height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
"""

_SCRIPT = """
const CATEGORIES = [
    { key: 'large_commit_no_test_changes', label: 'Large commits with no test changes',
      desc: '3+ production files changed, no test file touched' },
    { key: 'untested_file', label: 'Untested files',
      desc: 'Touched in this window, no matching test file found' },
    { key: 'possible_ai_usage_signals', label: 'Possible AI-usage signals',
      desc: 'Co-authored trailers, generic messages, boilerplate comments, hallucinated deps' },
    { key: 'oversized_file', label: 'Oversized files',
      desc: 'Over 500 lines' },
    { key: 'generic_naming_density', label: 'Generic naming density',
      desc: 'Files where >5% of lines use temp/tmp/data/value/result' },
];

let selectedPath = null;

function setStatus(msg, isError) {
    const el = document.getElementById('status');
    el.textContent = msg || '';
    el.className = isError ? 'error' : '';
}

async function pickFolder() {
    setStatus('');
    const path = await pywebview.api.pick_folder();
    if (!path) return;
    selectedPath = path;
    document.getElementById('pathLabel').textContent = path;
    document.getElementById('runBtn').disabled = false;
    document.getElementById('results').style.display = 'none';
}

async function runScan() {
    if (!selectedPath) return;
    const runBtn = document.getElementById('runBtn');
    runBtn.disabled = true;
    setStatus('Scanning... this can take a moment on larger repos.');
    document.getElementById('results').style.display = 'none';

    try {
        const summary = await pywebview.api.run_scan(selectedPath);
        if (summary.error) {
            setStatus(summary.error, true);
        } else {
            setStatus('');
            renderResults(summary);
        }
    } catch (err) {
        setStatus('Something went wrong running the scan: ' + err, true);
    } finally {
        runBtn.disabled = false;
    }
}

function renderResults(summary) {
    const maxValue = Math.max(1, ...CATEGORIES.map(c => summary[c.key] || 0));
    const list = document.getElementById('cardList');
    list.innerHTML = '';
    for (const cat of CATEGORIES) {
        const value = summary[cat.key] || 0;
        const pct = Math.round((value / maxValue) * 100);
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="label">${cat.label}<span class="desc">${cat.desc}</span></div>
            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
            <div class="count">${value}</div>
        `;
        list.appendChild(card);
    }
    document.getElementById('metaLine').textContent =
        `Scanned ${summary.files_scanned} files touched across ${summary.commits_scanned} commits over ${summary.window_label}`;
    document.getElementById('results').style.display = 'block';
}

window.addEventListener('pywebviewready', () => {
    document.getElementById('pickBtn').disabled = false;
});
"""

_BODY = """
<header>
    <div>
        <div class="brand">Burghley Scan</div>
        <div class="tagline">Free, offline scan for ungoverned AI-usage patterns</div>
    </div>
</header>
<main>
    <div class="panel">
        <div class="row">
            <button id="pickBtn" onclick="pickFolder()" disabled>Select repository...</button>
            <div class="path-label" id="pathLabel">No folder selected</div>
            <button id="runBtn" class="secondary" onclick="runScan()" disabled>Run scan</button>
        </div>
        <div id="status"></div>

        <div id="results">
            <div class="meta" id="metaLine"></div>
            <div id="cardList"></div>
            <div id="disclaimer">
                These are correlation signals, not proof. A high count can mean AI-assisted
                changes without review, or just a team that tests differently than this scan
                expects. Nothing shown here is uploaded or written to disk.
            </div>
            <div id="cta">
                This free tool shows you a pattern exists. The full audit shows you why, with
                detailed findings, plain-language manager reports, and a best-practices plan.
                <a href="https://burghley-ai-services.co.uk/contact" target="_blank">Get in touch</a>
                if this looks worth investigating.
            </div>
        </div>
    </div>
</main>
"""


def get_index_html() -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Burghley Scan</title>
<style>{_STYLE}</style>
</head>
<body>
{_BODY}
<script>{_SCRIPT}</script>
</body>
</html>"""
