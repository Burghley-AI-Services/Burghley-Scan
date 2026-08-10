"""
Builds the single self-contained HTML string for the GUI window.

Deliberately a single inline string, not separate .html/.css/.js files
loaded via url= - pywebview only starts its built-in local HTTP server
when a window is loaded from a local file/url. Loading from an inline
html= string never triggers that, so this stays true to the "zero
network calls, not even localhost" claim. See gui/app.py for the
pywebview wiring and the js_api bridge this page talks to.
"""

from gui.assets import LOGO_PNG_BASE64

VERSION = "1.0.0-lite"

# Colours and type pulled directly from the Burghley AI Services website's
# design tokens (app/globals.css) so the free tool and the site read as
# the same product. The site is dark-mode only, so this is too - no light
# theme to fall back to. Sharp corners (no border-radius) match the site's
# "no rounded corners" shape language; font stacks fall back to system
# fonts if Epilogue/Inter/JetBrains Mono aren't installed locally, since
# fetching webfonts would mean a network call.
_STYLE = """
:root {
    color-scheme: dark;
    --bg: #10141a;
    --panel: #1c2026;
    --panel-high: #262a31;
    --border: #21262d;
    --text: #dfe2eb;
    --text-variant: #d4c4b7;
    --muted: #8b949e;
    --accent: #f2be8c;
    --accent-fixed: #ffdcbd;
    --accent-container: #d4a373;
    --on-accent: #482904;
    --accent-dim: #7d562d;
    --danger: #ffb4ab;

    --font-headline: 'Epilogue', 'Segoe UI Semibold', -apple-system, sans-serif;
    --font-body: 'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    --font-mono: 'JetBrains Mono', Consolas, 'Courier New', monospace;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: var(--font-body);
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
header img.logo { height: 30px; width: auto; display: block; }
header .brand { font-family: var(--font-headline); font-weight: 700; font-size: 17px; letter-spacing: 0.01em; }
header .tagline { color: var(--muted); font-size: 13px; }
main { padding: 24px; max-width: 900px; margin: 0 auto; }

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 24px;
}

.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

button {
    font: inherit;
    font-weight: 600;
    background: var(--accent);
    color: var(--on-accent);
    border: none;
    padding: 10px 18px;
    cursor: pointer;
}
button:disabled { background: var(--accent-dim); color: var(--muted); cursor: not-allowed; }
button.secondary { background: transparent; border: 1px solid var(--border); color: var(--text); }

.path-label {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--muted);
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    flex: 1;
    min-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.path-label.invalid { color: var(--danger); border-color: var(--danger); }

#status { margin-top: 16px; color: var(--muted); font-size: 14px; display: none; align-items: center; gap: 10px; }
#status.visible { display: flex; }
#status.error { color: var(--danger); }
#status.loading { color: var(--text); }

#results { display: none; margin-top: 24px; }
#results .meta { color: var(--muted); font-size: 13px; margin-bottom: 20px; font-family: var(--font-mono); }

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
.card .bar-track { background: var(--bg); height: 10px; overflow: hidden; }
.card .bar-fill { background: var(--accent); height: 100%; transition: width 0.4s ease; }
.card .count { text-align: right; font-weight: 700; font-size: 16px; font-family: var(--font-headline); }

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
    background: rgba(242, 190, 140, 0.08);
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
let scanInProgress = false;

window.updateScanProgress = function(current, total) {
    if (!scanInProgress) return;
    setStatus(`Scanning - ${current}/${total} files...`, 'loading');
};

function setStatus(msg, kind) {
    // kind: 'error' | 'loading' | undefined (plain)
    // The spinner is a persistent DOM node, shown/hidden but never
    // recreated - replacing it (e.g. via innerHTML) on every progress
    // tick restarts its CSS animation from 0deg each time, which is what
    // made it look like it kept resetting instead of spinning smoothly.
    const el = document.getElementById('status');
    document.getElementById('statusSpinner').style.display = kind === 'loading' ? 'inline-block' : 'none';
    document.getElementById('statusText').textContent = msg || '';
    const stateClass = kind === 'error' ? 'error' : (kind === 'loading' ? 'loading' : '');
    el.className = (msg ? 'visible ' : '') + stateClass;
}

async function pickFolder() {
    setStatus('');
    const picked = await pywebview.api.pick_folder();
    if (!picked) return;
    const pathLabel = document.getElementById('pathLabel');
    pathLabel.textContent = picked.path;
    document.getElementById('results').style.display = 'none';

    if (picked.ok) {
        selectedPath = picked.path;
        pathLabel.classList.remove('invalid');
        document.getElementById('runBtn').disabled = false;
        setStatus('');
    } else {
        selectedPath = null;
        pathLabel.classList.add('invalid');
        document.getElementById('runBtn').disabled = true;
        setStatus(picked.message, 'error');
    }
}

async function runScan() {
    if (!selectedPath) return;
    const runBtn = document.getElementById('runBtn');
    const pickBtn = document.getElementById('pickBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    runBtn.disabled = true;
    pickBtn.disabled = true;
    cancelBtn.style.display = 'inline-block';
    cancelBtn.disabled = false;
    scanInProgress = true;
    setStatus('Scanning - this can take a moment on larger repos...', 'loading');
    document.getElementById('results').style.display = 'none';

    try {
        const summary = await pywebview.api.run_scan(selectedPath);
        if (summary.cancelled) {
            setStatus('Scan cancelled.');
        } else if (summary.error) {
            setStatus(summary.error, 'error');
        } else {
            setStatus('');
            renderResults(summary);
        }
    } catch (err) {
        setStatus('Something went wrong running the scan: ' + err, 'error');
    } finally {
        scanInProgress = false;
        runBtn.disabled = false;
        pickBtn.disabled = false;
        cancelBtn.style.display = 'none';
    }
}

async function cancelScan() {
    const cancelBtn = document.getElementById('cancelBtn');
    cancelBtn.disabled = true;
    setStatus('Cancelling...', 'loading');
    await pywebview.api.cancel_scan();
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

_BODY = f"""
<header>
    <img class="logo" src="data:image/png;base64,{LOGO_PNG_BASE64}" alt="Burghley AI Services">
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
            <button id="cancelBtn" class="secondary" onclick="cancelScan()" style="display: none;">Cancel</button>
        </div>
        <div id="status">
            <span class="spinner" id="statusSpinner" style="display: none;"></span>
            <span id="statusText"></span>
        </div>

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
<title>Burghley Scan - Preview</title>
<style>{_STYLE}</style>
</head>
<body>
{_BODY}
<script>{_SCRIPT}</script>
</body>
</html>"""
