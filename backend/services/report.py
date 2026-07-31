from datetime import datetime

def generate_html_report(project_path, health, analysis, rules, vulns, ai_reviews):
    score = health["overall"]
    cats = health["categories"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

    vuln_rows = "".join(
        f"<tr><td>{v['dependency']}</td><td>{v['cve']}</td>"
        f"<td>{v['description']}</td></tr>"
        for v in vulns["vulnerabilities"]
    ) or "<tr><td colspan='3'>No known vulnerabilities found</td></tr>"

    rec_items = "".join(f"<li>{r}</li>" for r in analysis["recommendations"])
    compose_items = "".join(
        f"<li class='{i['severity']}'><b>{i['file']}</b> — {i['issue']}</li>"
        for i in analysis["compose_issues"]
    ) or "<li>No Compose issues detected</li>"

    dup_items = "".join(
        f"<li><b>{d['file_a']}</b> line {d['line_a']} ↔ "
        f"<b>{d['file_b']}</b> line {d['line_b']}<br>"
        f"<code>{d['preview']}</code></li>"
        for d in analysis["duplicates"]
    ) or "<li>No significant duplication found</li>"

    cat_bars = "".join(
        f"""<div class="cat">
              <span>{name}</span>
              <div class="bar-wrap">
                <div class="bar" style="width:{val}%;
                  background:{'#22c55e' if val>=80 else '#f59e0b' if val>=60 else '#ef4444'}">
                  {val}
                </div>
              </div>
           </div>"""
        for name, val in cats.items()
    )

    ai_section = "".join(
        f"<h3>{role.title()} Review</h3><pre>{text}</pre>"
        for role, text in ai_reviews.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Android Intelligence Report</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f172a;
          color: #e2e8f0; max-width: 960px; margin: 0 auto; padding: 32px; }}
  h1 {{ color: #6ee7b7; }} h2 {{ color: #94a3b8; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }}
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
</style>
</head>
<body>
<h1>🤖 Android Intelligence Report</h1>
<p class="meta">Project: {project_path} &nbsp;|&nbsp; Generated: {now}</p>

<div class="badge">
  <div class="score">{score}</div>
  <div>Overall Health Score / 100</div>
</div>

<h2>Category Breakdown</h2>
{cat_bars}

<h2>Project Overview</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Kotlin Files</td><td>{analysis['kotlin_files']}</td></tr>
  <tr><td>Architecture Pattern</td><td>{analysis['arch_pattern']}</td></tr>
  <tr><td>ViewModels</td><td>{analysis['viewmodels']}</td></tr>
  <tr><td>Repositories</td><td>{analysis['repositories']}</td></tr>
  <tr><td>Use Cases</td><td>{analysis['use_cases']}</td></tr>
  <tr><td>Composable functions</td><td>{analysis['compose']}</td></tr>
  <tr><td>Test files</td><td>{analysis['tests']}</td></tr>
  <tr><td>Total lines of code</td><td>{analysis['total_lines']:,}</td></tr>
</table>

<h2>Recommendations</h2>
<ul>{rec_items}</ul>

<h2>Security — Dependency Vulnerabilities</h2>
<p>Scanned {vulns['scanned']} dependencies</p>
<table><tr><th>Dependency</th><th>CVE</th><th>Description</th></tr>
{vuln_rows}</table>

<h2>Compose Recomposition Issues</h2>
<ul>{compose_items}</ul>

<h2>Code Duplication</h2>
<ul>{dup_items}</ul>

<h2>AI Review</h2>
{ai_section}
</body></html>"""
    return html

def save_pdf(html, path="aia_report.pdf"):
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(path)
        return path
    except ImportError:
        return None