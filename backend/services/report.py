from datetime import datetime
from html import escape
from io import BytesIO
from typing import Dict, List, Optional, Tuple


def _detect_arch(analysis: Dict) -> str:
    vms = analysis.get("viewmodels", 0)
    repos = analysis.get("repositories", 0)
    if vms > 0 and repos > 0:
        return "MVVM with Repository Pattern"
    if vms > 0:
        return "MVVM (partial — no Repository)"
    return "Unknown — consider MVVM"


def _build_recommendations(analysis: Dict, rules: Dict) -> List[str]:
    recs = list(analysis.get("recommendations") or [])
    if recs:
        return recs

    if rules.get("todos", 0) > 0:
        recs.append(f"{rules['todos']} TODO comment(s) — resolve or track them")
    if rules.get("fixmes", 0) > 0:
        recs.append(f"{rules['fixmes']} FIXME comment(s) — address before release")
    if rules.get("printlns", 0) > 0:
        recs.append(f"{rules['printlns']} println() call(s) — switch to proper logging")
    if rules.get("null_assertions", 0) > 0:
        recs.append(f"{rules['null_assertions']} !! null assertion(s) — prefer safe calls")
    if analysis.get("viewmodels", 0) == 0:
        recs.append("No ViewModels detected — implement MVVM")
    if analysis.get("repositories", 0) == 0:
        recs.append("No Repository layer detected — consider Clean Architecture")
    if analysis.get("tests", 0) == 0:
        recs.append("No tests detected — add unit/UI coverage")
    if not recs:
        recs.append("No major rule-based recommendations — review AI findings if available")
    return recs


def generate_html_report(
    project_path,
    health,
    analysis,
    rules,
    vulns,
    ai_reviews,
    technologies=None,
):
    """Build a self-contained HTML report from AppForge analysis results."""
    score = health.get("overall", 0)
    cats = health.get("categories", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

    vulns = vulns or {}
    rules = rules or {}
    analysis = analysis or {}
    ai_reviews = ai_reviews or {}
    technologies = technologies or analysis.get("technologies") or {}

    vuln_rows = "".join(
        f"<tr><td>{escape(str(v.get('dependency', '')))}</td>"
        f"<td>{escape(str(v.get('cve', '')))}</td>"
        f"<td>{escape(str(v.get('description', '')))}</td></tr>"
        for v in vulns.get("vulnerabilities", [])
    ) or "<tr><td colspan='3'>No known vulnerabilities found</td></tr>"

    rec_items = "".join(
        f"<li>{escape(str(r))}</li>" for r in _build_recommendations(analysis, rules)
    )

    compose_items = "".join(
        f"<li class='{escape(str(i.get('severity', 'info')))}'>"
        f"<b>{escape(str(i.get('file', '')))}</b> — {escape(str(i.get('issue', '')))}</li>"
        for i in analysis.get("compose_issues", [])
    ) or "<li>No Compose issues detected</li>"

    dup_items = "".join(
        f"<li><b>{escape(str(d.get('file_a', '')))}</b> line {d.get('line_a', '?')} ↔ "
        f"<b>{escape(str(d.get('file_b', '')))}</b> line {d.get('line_b', '?')}<br>"
        f"<code>{escape(str(d.get('preview', '')))}</code></li>"
        for d in analysis.get("duplicates", [])
    ) or "<li>No significant duplication found</li>"

    security_items = "".join(
        f"<li><b>{escape(str(s.get('issue', '')))}</b> — "
        f"{escape(str(s.get('file', '')))} ({s.get('count', 0)}×)</li>"
        for s in rules.get("security_issues", [])
    ) or "<li>No hardcoded secrets / weak crypto patterns detected</li>"

    deprecated_items = "".join(
        f"<li><code>{escape(str(d.get('api', '')))}</code> in "
        f"<b>{escape(str(d.get('file', '')))}</b></li>"
        for d in rules.get("deprecated_apis", [])
    ) or "<li>No deprecated APIs found</li>"

    tech_items = "".join(
        f"<li>{'✅' if found else '❌'} {escape(str(name))}</li>"
        for name, found in technologies.items()
    ) or "<li>No technology signals detected</li>"

    cat_bars = "".join(
        f"""<div class="cat">
              <span>{escape(str(name))}</span>
              <div class="bar-wrap">
                <div class="bar" style="width:{int(val)}%;
                  background:{'#22c55e' if val >= 80 else '#f59e0b' if val >= 60 else '#ef4444'}">
                  {int(val)}
                </div>
              </div>
           </div>"""
        for name, val in cats.items()
    )

    role_titles = {
        "analyzer": "Architecture Assessment",
        "fixer": "Security Assessment",
        "reviewer": "Performance & Release Readiness",
    }
    ai_section = "".join(
        f"<h3>{escape(role_titles.get(str(role), str(role).replace('_', ' ').title()))}</h3>"
        f"<pre>{escape(str(text))}</pre>"
        for role, text in ai_reviews.items()
        if role != "error"
    ) or "<p>No AI review available for this run.</p>"

    if "error" in ai_reviews:
        ai_section = f"<p class='warn'>{escape(str(ai_reviews['error']))}</p>" + ai_section

    arch = _detect_arch(analysis)
    total_lines = analysis.get("total_lines", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AppForge — Android Intelligence Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #0f172a; color: #e2e8f0; max-width: 960px;
          margin: 0 auto; padding: 32px; }}
  h1 {{ color: #6ee7b7; }}
  h2 {{ color: #94a3b8; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }}
  h3 {{ color: #7dd3fc; }}
  .score {{ font-size: 72px; font-weight: 700; color: {color}; }}
  .badge {{ background: #1e293b; border-radius: 8px; padding: 16px 24px; margin: 8px 0; }}
  .cat {{ display:flex; align-items:center; gap:12px; margin:6px 0; font-size:14px; }}
  .bar-wrap {{ flex:1; background:#1e293b; border-radius:4px; height:22px; }}
  .bar {{ height:22px; border-radius:4px; color:#0f172a; font-weight:700;
          font-size:12px; line-height:22px; padding-left:8px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:#1e293b; padding:8px; text-align:left; }}
  td {{ padding:8px; border-bottom:1px solid #1e293b; font-size:13px; }}
  pre {{ background:#1e293b; padding:16px; border-radius:8px;
         white-space:pre-wrap; font-size:13px; line-height:1.6; }}
  li {{ margin: 6px 0; line-height:1.5; }}
  li.error {{ color:#f87171; }} li.warning {{ color:#fbbf24; }} li.info {{ color:#60a5fa; }}
  .meta {{ color:#64748b; font-size:13px; }}
  .warn {{ color:#fbbf24; }}
  .footer {{ margin-top: 40px; color:#64748b; font-size:12px; }}
</style>
</head>
<body>
<h1>AppForge — Android Intelligence Report</h1>
<p class="meta">Project: {escape(str(project_path))} &nbsp;|&nbsp; Generated: {now}</p>

<div class="badge">
  <div class="score">{score}</div>
  <div>Overall Health Score / 100</div>
</div>

<h2>Category Breakdown</h2>
{cat_bars}

<h2>Project Overview</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Kotlin / Java source files</td><td>{analysis.get('kotlin_files', 0)}</td></tr>
  <tr><td>Architecture Pattern</td><td>{escape(arch)}</td></tr>
  <tr><td>ViewModels</td><td>{analysis.get('viewmodels', 0)}</td></tr>
  <tr><td>Repositories</td><td>{analysis.get('repositories', 0)}</td></tr>
  <tr><td>Test files / @Test usage</td><td>{analysis.get('tests', 0)}</td></tr>
  <tr><td>Total lines of code</td><td>{total_lines:,}</td></tr>
  <tr><td>TODOs</td><td>{rules.get('todos', 0)}</td></tr>
  <tr><td>FIXMEs</td><td>{rules.get('fixmes', 0)}</td></tr>
  <tr><td>println() calls</td><td>{rules.get('printlns', 0)}</td></tr>
  <tr><td>Null assertions (!!)</td><td>{rules.get('null_assertions', 0)}</td></tr>
</table>

<h2>Technology Stack</h2>
<ul>{tech_items}</ul>

<h2>Recommendations</h2>
<ul>{rec_items}</ul>

<h2>Security — Dependency Vulnerabilities</h2>
<p>Scanned {vulns.get('scanned', 0)} dependencies</p>
<table><tr><th>Dependency</th><th>CVE</th><th>Description</th></tr>
{vuln_rows}</table>

<h2>Security — Code Patterns</h2>
<ul>{security_items}</ul>

<h2>Deprecated APIs</h2>
<ul>{deprecated_items}</ul>

<h2>Compose Recomposition Issues</h2>
<ul>{compose_items}</ul>

<h2>Code Duplication</h2>
<ul>{dup_items}</ul>

<h2>AI Review</h2>
{ai_section}

<p class="footer">Generated by AppForge · Local Android Code Intelligence · © 2026</p>
</body>
</html>"""
    return html


def save_pdf(html, path="aia_report.pdf") -> Optional[str]:
    """Write PDF to disk. Returns path on success, None if WeasyPrint missing."""
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(path)
        return path
    except ImportError:
        return None
    except Exception:
        return None


def generate_pdf_bytes(html: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Render PDF in-memory for Streamlit download_button.
    Returns (pdf_bytes, error_message).
    """
    try:
        from weasyprint import HTML
        buf = BytesIO()
        HTML(string=html).write_pdf(buf)
        return buf.getvalue(), None
    except ImportError:
        return None, "WeasyPrint is not installed. Run: pip install weasyprint"
    except Exception as e:
        return None, f"PDF generation failed: {e}"
