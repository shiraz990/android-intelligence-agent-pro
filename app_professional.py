import streamlit as st

# ── set_page_config MUST be the absolute first st. command ─────
st.set_page_config(
    page_title="AppForge",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SESSION STATE INIT (no rendering, safe after set_page_config)
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "fixes" not in st.session_state:
    st.session_state.fixes = []
if "applied_fixes" not in st.session_state:
    st.session_state.applied_fixes = set()
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "project_path" not in st.session_state:
    st.session_state.project_path = ""

import os
import sys
import traceback
import plotly.graph_objects as go
from datetime import datetime
from typing import Tuple, List, Dict, Optional
import subprocess
import platform
import base64

sys.path.insert(0, os.getcwd())

from backend.services.scanner import scan_project
from backend.services.rules_engine import analyze_rules
from backend.services.analyzer import detect_technologies, detect_duplicates, analyze_compose
from backend.services.vulnerability import scan_vulnerabilities
from backend.services.health_score import calculate_health_score
from backend.services.ai_reviewer import review_project, get_model_info, role_display_label
from backend.services.auto_fixer import AutoFixEngine
from backend.services.report import generate_html_report, generate_pdf_bytes
from backend.services.grounded_assessment import build_grounded_assessments


# ── SAFE FOLDER PICKER (No tkinter) ──────────────────────────
def open_file_explorer():
    """Open file explorer at a default location"""
    try:
        home = os.path.expanduser("~")
        if platform.system() == "Windows":
            os.startfile(home)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", home])
        else:  # Linux
            subprocess.Popen(["xdg-open", home])
        return True
    except Exception as e:
        st.error(f"Could not open file explorer: {e}")
        return False


# ── LOGO ───────────────────────────────────────────────────────
CUSTOM_LOGO_SVG = '''<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
<defs>
    <radialGradient id="bg" cx="35%" cy="30%" r="80%">
      <stop offset="0%" stop-color="#151E32"/>
      <stop offset="100%" stop-color="#0A0F1E"/>
    </radialGradient>
    <linearGradient id="chip" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#22D3EE"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
</defs>
<rect x="24" y="24" width="464" height="464" rx="100" fill="url(#bg)" stroke="#1E293B" stroke-width="2"/>
<g stroke="url(#chip)" stroke-width="7" stroke-linecap="round" opacity="0.85">
  <line x1="256" y1="106" x2="256" y2="66"/>
  <line x1="386" y1="181" x2="426" y2="158"/>
  <line x1="386" y1="331" x2="426" y2="354"/>
  <line x1="256" y1="406" x2="256" y2="446"/>
  <line x1="126" y1="331" x2="86" y2="354"/>
  <line x1="126" y1="181" x2="86" y2="158"/>
</g>
<g fill="url(#chip)">
  <circle cx="256" cy="58" r="9"/><circle cx="434" cy="153" r="9"/>
  <circle cx="434" cy="359" r="9"/><circle cx="256" cy="454" r="9"/>
  <circle cx="78" cy="359" r="9"/><circle cx="78" cy="153" r="9"/>
</g>
<polygon points="256,106 386,181 386,331 256,406 126,331 126,181"
         fill="none" stroke="url(#chip)" stroke-width="10" stroke-linejoin="round"/>
<polyline points="225,190 170,256 225,322" fill="none" stroke="url(#chip)"
          stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="287,190 342,256 287,322" fill="none" stroke="url(#chip)"
          stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="212,262 243,293 302,218" fill="none" stroke="#34D399"
          stroke-width="20" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
</svg>'''

# ── STYLES ─────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem; border-radius: 15px; color: white;
    margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(102,126,234,0.3);
}
.main-header h1 { font-size: 2.5rem; font-weight: 700; margin: 0; }
.main-header p  { font-size: 1.1rem; opacity: 0.9; margin: 0.5rem 0 0 0; }
.sidebar-logo { text-align: center; padding: 15px 0; margin-bottom: 10px; }
.sidebar-logo svg { 
    width: 80px;
    height: 80px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(34, 211, 238, 0.15);
}
.sidebar-logo h3 { 
    color: #667eea; 
    margin: 8px 0 3px 0;
    font-weight: 700; 
    font-size: 22px;
}
.sidebar-logo p  { 
    font-size: 13px;
    color: #8B5CF6; 
    margin: 0; 
    font-weight: 500; 
}
.status-badge {
    display: inline-block;
    background: linear-gradient(135deg, #22D3EE, #8B5CF6);
    color: white; padding: 2px 10px; border-radius: 10px;
    font-size: 11px;
    font-weight: 600; margin-top: 4px;
}
/* ── SIDEBAR TOGGLE LABELS ── */
.stToggle label {
    font-size: 15px !important;
    font-weight: 500;
}

/* ── SIDEBAR INFO BOX ── */
.sidebar-info {
    background: #f0f4ff;
    padding: 12px 14px;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    font-size: 14px !important;
    line-height: 1.6;
}
.sidebar-info code {
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛠️ AppForge</h1>
    <p>🧠 AI-Powered Android Code Review — On Your Machine</p>
    <p style="font-size:0.9rem;opacity:0.8;">
        🛠️ Forge better Android code · 🔒  Zero cloud · 🧠 Three AI models
    </p>
</div>
""", unsafe_allow_html=True)


# ── SIDEBAR ────────────────────────────────────────────────────
def _check_ollama() -> Tuple[bool, List[str]]:
    try:
        r = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            models = [
                line.split()[0]
                for line in r.stdout.strip().splitlines()[1:]
                if line.strip()
            ]
            return True, models
        return False, []
    except Exception:
        return False, []


OLLAMA_RUNNING, OLLAMA_MODELS = _check_ollama()

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo">
        {CUSTOM_LOGO_SVG}
        <h3>AppForge</h3>
        <p>Core Edition v1.0</p>
        <span class="status-badge">🛠️FORGING</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Forge Settings")
    run_ai = st.toggle("🧠 AI Review", value=True)
    run_auto_fix = st.toggle("🔧 Auto-Fix Suggestions", value=True)
    run_vulns = st.toggle("🛡️ CVE Scanning-(Common Vulnerabilities and Exposures)", value=True)
    run_compose = st.toggle("🎨 Compose Analysis", value=True)

    st.markdown("---")
    st.markdown("### 🧠 Model Council")
    try:
        model_info = get_model_info()
        st.info(f"""
- 🏗 **{model_info['analyzer']['name']}** — Architecture Assessment
- 🛡 **{model_info['fixer']['name']}** — Security Assessment
- ⚡ **{model_info['reviewer']['name']}** — Performance & Release Readiness
        """)
    except Exception:
        st.info("""
- 🏗 **deepseek-coder:1.3b** — Architecture
- 🛡 **qwen2.5-coder:3b** — Security
- ⚡ **gemma2:2b** — Performance
        """)

    st.markdown("---")
    st.markdown("### 🖥 Ollama Status")
    if OLLAMA_RUNNING:
        st.success("✅ Ollama Running")
        if OLLAMA_MODELS:
            with st.expander("Installed models", expanded=False):
                for m in OLLAMA_MODELS:
                    st.caption(f"• {m}")
        else:
            st.caption("No models pulled yet — run `ollama pull <model>`")
    else:
        st.error("❌ Ollama Not Found")
        st.caption("Start it with:")
        st.code("ollama serve", language="bash")

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    applied_count = len(st.session_state.applied_fixes)
    st.caption(f"Issues fixed this session: **{applied_count}**")
    st.caption(f"Analysis ready: **{'Yes' if st.session_state.analysis_done else 'No'}**")

# ── PROJECT PATH (Truly Cross-Platform) ──────────────────────
st.markdown("### 📁 Load Your Project")

# Show current path status
if st.session_state.project_path and os.path.exists(st.session_state.project_path):
    st.success(f"✅ Path exists: {st.session_state.project_path}")
elif st.session_state.project_path:
    st.warning(f"⚠️ Path does not exist: {st.session_state.project_path}")

# Simple path input with helper buttons (Works on ALL platforms)
st.markdown("#### Project path")

# Path input with helper buttons
col1, col2, col3 = st.columns([5, 1, 1])

with col1:
    project_path = st.text_input(
        "Project Path",
        value=st.session_state.get('project_path', ''),
        placeholder="Enter the full path to your Android project",
        help="Example: C:\\Users\\username\\AndroidStudioProjects\\MyApp",
        key="project_path_input"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("📂 Browse", use_container_width=True):
        if open_file_explorer():
            st.info("📂 File explorer opened. Copy the path and paste it above.")

with col3:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("↺ Clear", use_container_width=True):
        st.session_state.project_path = ""
        st.rerun()

# Save to session state
if project_path:
    st.session_state.project_path = project_path

# ── QUICK PATH SUGGESTIONS (Cross-Platform) ──────────────────
with st.expander("💡 Recent Projects", expanded=False):
    st.markdown("**Common Android project locations:**")

    # Detect OS and set appropriate paths
    current_os = platform.system()
    home = os.path.expanduser("~")

    if current_os == "Windows":
        common_paths = [
            os.path.join(home, "AndroidStudioProjects"),
            os.path.join(home, "Documents", "AndroidStudioProjects"),
            os.path.join(home, "Desktop", "AndroidStudioProjects"),
            os.path.join(home, "source", "Android"),
            os.path.join(home, "IdeaProjects"),
            "C:\\AndroidProjects",
            "D:\\AndroidProjects",
        ]
    else:  # macOS / Linux
        common_paths = [
            os.path.join(home, "AndroidStudioProjects"),
            os.path.join(home, "Documents", "Android"),
            os.path.join(home, "Android"),
            os.path.join(home, "Desktop", "Android"),
            os.path.join(home, "source", "Android"),
            os.path.join(home, "IdeaProjects"),
        ]

    # Find existing paths
    existing_paths = []
    for path in common_paths:
        if os.path.exists(path):
            existing_paths.append(path)
            # Also show subdirectories (limited to avoid slowness)
            try:
                items = list(os.listdir(path))[:10]  # Limit to 10 items
                for item in items:
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        # Check if it looks like an Android project
                        if os.path.exists(os.path.join(full_path, "app")) or \
                                os.path.exists(os.path.join(full_path, "build.gradle")):
                            existing_paths.append(full_path)
            except:
                pass

    # Remove duplicates and limit
    existing_paths = list(dict.fromkeys(existing_paths))[:10]

    if existing_paths:
        st.markdown("**Click a path below to auto-fill:**")

        for i, path in enumerate(existing_paths):
            unique_key = f"suggest_{i}_{hash(path) % 1000000}"
            if st.button(f"📁 {path}", key=unique_key):
                st.session_state.project_path = path
                st.rerun()
    else:
        st.info("No Android projects found in common locations.")
        st.markdown("""
        **Tips for finding your project:**
        1. Open your Android Studio project
        2. Right-click on the project name in the Project panel
        3. Select "Show in Explorer" (Windows) or "Show in Finder" (macOS)
        4. Copy the path from the address bar
        """)

    st.markdown("---")
    st.markdown("**Example paths:**")
    if current_os == "Windows":
        st.code("C:\\Users\\username\\AndroidStudioProjects\\MyApp", language="text")
        st.code("D:\\AndroidProjects\\MyApp", language="text")
    else:
        st.code("/Users/username/AndroidStudioProjects/MyApp", language="text")
        st.code("/Users/username/Documents/Android/MyApp", language="text")

st.markdown("---")

# ── ANALYZE BUTTON ────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    analyze_btn = st.button("🚀 Analyze Project", type="primary", use_container_width=True)
with col2:
    if st.button("🗑 Clear & Reset", use_container_width=True):
        st.session_state.analysis_done = False
        st.session_state.fixes = []
        st.session_state.applied_fixes = set()
        st.session_state.analysis_results = {}
        st.rerun()

# ══════════════════════════════════════════════════════════════
# ANALYSIS BLOCK
# ══════════════════════════════════════════════════════════════
if analyze_btn:
    if not project_path:
        st.error("❌ Please enter or select a project path first!")
        st.stop()

    if not os.path.exists(project_path):
        st.error(f"❌ Path does not exist: {project_path}")
        st.stop()

    st.session_state.applied_fixes = set()

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.info("🔍 Scanning project files...")
        progress_bar.progress(10)
        project = scan_project(project_path)

        if len(project["files"]) == 0:
            st.error("No Kotlin/Java files found. Check the path.")
            st.stop()

        status_text.info("📊 Analyzing code structure...")
        progress_bar.progress(25)
        rules = analyze_rules(project["files"])

        status_text.info("🏗 Detecting architecture patterns...")
        progress_bar.progress(40)
        gradle_text = "\n".join(project["gradle_files"]) + "\n" + project["toml"]
        technologies = detect_technologies(gradle_text)
        duplicates = detect_duplicates(project["files"])
        compose_issues = analyze_compose(project["files"]) if run_compose else []

        kotlin_files = viewmodels = repositories = tests = 0
        for file in project["files"]:
            if file["type"] not in ["kotlin", "java"]:
                continue
            kotlin_files += 1
            code = file["content"]
            if "viewmodel" in file["name"].lower() or "ViewModel" in code: viewmodels += 1
            if "repository" in file["name"].lower() or "Repository" in code: repositories += 1
            if "@Test" in code or "@test" in code.lower():                      tests += 1

        analysis = {
            "kotlin_files": kotlin_files,
            "viewmodels": viewmodels,
            "repositories": repositories,
            "tests": tests,
            "technologies": technologies,
            "duplicates": duplicates,
            "compose_issues": compose_issues,
            "total_lines": sum(f["lines"] for f in project["files"]),
            "recommendations": []
        }

        vulns = {"dependencies": [], "vulnerabilities": [], "scanned": 0}
        if run_vulns:
            status_text.info("🔒 Scanning dependencies for CVEs...")
            progress_bar.progress(55)
            vulns = scan_vulnerabilities(project["gradle_files"], project["toml"])

        status_text.info("📈 Calculating health score...")
        progress_bar.progress(65)
        health = calculate_health_score(analysis, rules, vulns)

        ai_reviews = {}
        grounded = build_grounded_assessments(
            project_path=project_path,
            analysis=analysis,
            rules=rules,
            vulns=vulns,
            health=health,
            technologies=technologies,
            duplicates=duplicates,
            compose_issues=compose_issues,
        )

        if run_ai:
            status_text.info("🧠 Building project-specific assessment (AI polish)...")
            progress_bar.progress(75)
            tech_on = ", ".join(k for k, v in technologies.items() if v) or "None detected"
            tech_off = ", ".join(k for k, v in technologies.items() if not v) or "None"
            compose_lines = "; ".join(
                f"{i['file']}: {i['issue']}" for i in compose_issues[:8]
            ) or "None"
            deprecated_lines = "; ".join(
                f"{d['api']} in {d['file']}" for d in rules.get("deprecated_apis", [])[:8]
            ) or "None"
            sec_lines = "; ".join(
                f"{s['issue']} in {s['file']}" for s in rules.get("security_issues", [])[:8]
            ) or "None"
            vuln_lines = "; ".join(
                f"{v.get('cve', '?')} ({v.get('dependency', '?')})"
                for v in vulns.get("vulnerabilities", [])[:8]
            ) or "None"
            dup_count = len(duplicates)
            complex_files = ", ".join(
                f"{c['file']}({c['complexity']})"
                for c in rules.get("complex_files", [])[:6]
            ) or "None"
            cats = health.get("categories", {})
            cat_line = ", ".join(f"{k}={v}" for k, v in cats.items())
            if viewmodels > 0 and repositories > 0:
                arch = "MVVM with Repository"
            elif viewmodels > 0:
                arch = "MVVM partial (no Repository)"
            else:
                arch = "Architecture unclear / not MVVM"

            summary = f"""
SCOPE: Static analysis only. Every finding must cite numbers/files from THIS project.

PROJECT METRICS
- Path: {project_path}
- Kotlin/Java source files: {kotlin_files}
- Total lines: {analysis['total_lines']}
- Detected architecture: {arch}
- ViewModels: {viewmodels} | Repositories: {repositories} | Tests (@Test): {tests}
- Technologies present: {tech_on}
- Technologies absent: {tech_off}

HEALTH SCORE
- Overall: {health['overall']}/100
- Categories: {cat_line}

CODE QUALITY SIGNALS
- TODOs: {rules['todos']} | FIXMEs: {rules['fixmes']}
- println(): {rules['printlns']} | Log.d(): {rules.get('logd', 0)}
- Null assertions (!!): {rules['null_assertions']}
- HTTP URLs: {rules.get('http_urls', 0)} | Large files (>300 LOC): {rules.get('large_files', 0)}
- Duplicate code blocks found: {dup_count}
- High-complexity files: {complex_files}
- Deprecated APIs: {deprecated_lines}

SECURITY SIGNALS
- CVE findings: {len(vulns.get('vulnerabilities', []))} (deps scanned: {vulns.get('scanned', 0)})
- CVE details: {vuln_lines}
- Secret/weak-crypto patterns: {sec_lines}

COMPOSE SIGNALS
- Issues: {compose_lines}
"""[:3500]
            try:
                ai_status = st.empty()
                ai_status.info("⏳ Polishing project-grounded assessment with local models...")
                ai_reviews = review_project(summary, grounded=grounded)
                ai_status.empty()
            except Exception as e:
                st.warning(f"AI polish unavailable ({e}). Using project-grounded assessment.")
                ai_reviews = grounded
        else:
            # Still produce a project-specific narrative for Export / Assessment tab
            ai_reviews = grounded
            status_text.info("📋 Built project-specific assessment (AI polish disabled)")
            progress_bar.progress(75)

        fixes = []
        if run_auto_fix:
            status_text.info("🔧 Generating auto-fix suggestions...")
            progress_bar.progress(90)
            fixer = AutoFixEngine(project_path=project_path)
            for file in project["files"]:
                if file["type"] not in ["kotlin", "java"]:
                    continue
                code = file["content"]
                file_path = file["path"]
                issues = []
                if "http://" in code and "https://" not in code: issues.append({"type": "http_url", "severity": "high"})
                if "TODO" in code:                             issues.append({"type": "todo", "severity": "medium"})
                if "!!" in code:                             issues.append(
                    {"type": "null_assertion", "severity": "high"})
                if "println(" in code:                             issues.append({"type": "println", "severity": "low"})
                if issues:
                    fixes.extend(fixer.generate_fixes(file_path, code, issues))

        progress_bar.progress(100)
        status_text.success("✅ Analysis complete!")
        progress_bar.empty()
        status_text.empty()

        st.session_state.analysis_done = True
        st.session_state.fixes = fixes
        st.session_state.analysis_results = {
            "project": project,
            "analysis": analysis,
            "rules": rules,
            "vulns": vulns,
            "health": health,
            "ai_reviews": ai_reviews,
            "technologies": technologies,
            "viewmodels": viewmodels,
            "repositories": repositories,
            "tests": tests,
            "compose_issues": compose_issues,
            "duplicates": duplicates,
            "project_path": project_path,
            "kotlin_files": kotlin_files,
        }

    except Exception as e:
        st.error(f"❌ Analysis error: {e}")
        st.code(traceback.format_exc())
        st.stop()

# ══════════════════════════════════════════════════════════════
# DISPLAY BLOCK
# ══════════════════════════════════════════════════════════════
if not st.session_state.analysis_done:
    st.info("👆 Enter your Android project path above and click **Analyze Project** to begin.")
    st.stop()

r = st.session_state.analysis_results
project = r["project"]
analysis = r["analysis"]
rules = r["rules"]
vulns = r["vulns"]
health = r["health"]
ai_reviews = r["ai_reviews"]
technologies = r["technologies"]
viewmodels = r["viewmodels"]
repositories = r["repositories"]
tests = r["tests"]
compose_issues = r["compose_issues"]
duplicates = r["duplicates"]
_project_path = r["project_path"]
kotlin_files = r["kotlin_files"]
fixes_list = st.session_state.fixes

score = health["overall"]
if score >= 80:
    st.success(f"### 🟢 Overall Health Score: {score}/100")
    st.caption("✅ Project is in good health!")
elif score >= 60:
    st.warning(f"### 🟡 Overall Health Score: {score}/100")
    st.caption("⚠️ Some areas need attention.")
else:
    st.error(f"### 🔴 Overall Health Score: {score}/100")
    st.caption("🚨 Critical issues found — immediate action recommended.")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📄 Total Files", len(project["files"]))
col2.metric("📝 Kotlin Files", kotlin_files)
col3.metric("📊 Total Lines", f"{analysis['total_lines']:,}")
col4.metric("🧪 Tests", tests)
col5.metric("🔒 CVEs Found", len(vulns["vulnerabilities"]))

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview", "🏗 Architecture", "🛡 Security",
    "🎨 Compose", "📋 Assessment", "🔧 Auto-Fix", "📄 Export"
])

# ── TAB 1: Overview ───────────────────────────────────────────
with tab1:
    cats = health["categories"]
    fig = go.Figure(go.Scatterpolar(
        r=list(cats.values()),
        theta=list(cats.keys()),
        fill="toself",
        line_color="#667eea",
        fillcolor="rgba(102,126,234,0.2)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#2c3e50",
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🛠️ Technology Stack")
    cols = st.columns(4)
    for i, (tech, found) in enumerate(list(technologies.items())[:16]):
        (cols[i % 4].success if found else cols[i % 4].error)(
            f"{'✅' if found else '❌'} {tech}"
        )

    st.markdown("### 📌 Recommendations")
    if rules.get("todos", 0) > 0: st.warning(f"⚠ **{rules['todos']} TODO comments**")
    if rules.get("fixmes", 0) > 0: st.warning(f"⚠ **{rules['fixmes']} FIXME comments**")
    if rules.get("printlns", 0) > 0: st.warning(f"⚠ **{rules['printlns']} println() calls** — use proper logging")
    if rules.get("null_assertions", 0) > 0: st.warning(
        f"⚠ **{rules['null_assertions']} !! null assertions** — use safe calls")
    if viewmodels == 0: st.error("🚨 **No ViewModels** — implement MVVM")
    if repositories == 0: st.error("🚨 **No Repository layer** — consider Clean Architecture")

# ── TAB 2: Architecture ───────────────────────────────────────
with tab2:
    st.markdown("### 🏗 Architecture Analysis")
    c1, c2, c3 = st.columns(3)
    c1.metric("ViewModels", viewmodels)
    c2.metric("Repositories", repositories)
    c3.metric("Tests", tests)

    if viewmodels > 0 and repositories > 0:
        arch = "MVVM with Repository Pattern ✅"
    elif viewmodels > 0:
        arch = "MVVM (partial — no Repository) ⚠️"
    else:
        arch = "Unknown — consider MVVM 🚨"
    st.info(f"**Detected Architecture:** {arch}")

    st.markdown("### 📑 Code Duplication")
    if duplicates:
        for d in duplicates[:5]:
            with st.expander(f"{d['file_a']} ↔ {d['file_b']}"):
                st.code(d["preview"], language="kotlin")
                st.caption(f"Line {d['line_a']} ↔ Line {d['line_b']}")
    else:
        st.success("✅ No significant duplication detected")

    st.markdown("### ⚠️ Deprecated APIs")
    deps = rules.get("deprecated_apis", [])
    if deps:
        for d in deps:
            st.error(f"`{d['api']}` in **{d['file']}**")
    else:
        st.success("✅ No deprecated APIs found")


# ── TAB 3: Security ───────────────────────────────────────────
with tab3:
    st.markdown("### 🛡️ Security Analysis")

    if not run_vulns:
        st.info("⏭️ **CVE Scanning was disabled** during analysis.")
        st.caption("💡 To enable: Go to sidebar → toggle '🛡️ CVE Scanning' → re-run analysis")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("CVEs Found", len(vulns.get("vulnerabilities", [])))
        c2.metric("Dependencies Scanned", vulns.get("scanned", 0))
        c3.metric("API Keys Leaked", rules.get("api_keys", 0))

        if vulns.get("vulnerabilities"):
            for v in vulns["vulnerabilities"]:
                with st.expander(f"🚨 {v.get('cve', '?')} — {v.get('dependency', '?')}"):
                    st.write(v.get("description", "No description"))
                    st.caption(f"Severity: {v.get('severity', 'Unknown')} · Source: {v.get('source', '')}")
        else:
            st.success("✅ No known CVEs found")

    if rules.get("security_issues", []):
        st.subheader("🔐 Security Issues in Code")
        for issue in rules["security_issues"]:
            st.error(f"{issue['issue']} — **{issue['file']}** ({issue['count']}×)")

# ── TAB 4: Compose ────────────────────────────────────────────
with tab4:
    st.markdown("### 🎨 Jetpack Compose Analysis")

    if not run_compose:
        st.info("⏭️ **Compose Analysis was disabled** during analysis.")
        st.caption("💡 To enable: Go to sidebar → toggle '🎨 Compose Analysis' → re-run analysis")
    elif compose_issues:
        st.warning(f"Found {len(compose_issues)} Compose issue(s)")
        for issue in compose_issues:
            fn = {"error": st.error, "warning": st.warning}.get(issue["severity"], st.info)
            fn(f"**{issue['file']}** — {issue['issue']}")
    else:
        st.success("✅ No Compose recomposition issues detected")
# ── TAB 5: AI Review ──────────────────────────────────────────

# ── TAB 5: AI Review ──────────────────────────────────────────
with tab5:
    st.markdown("### 🧠 Project Assessment")
    st.caption(
        "Findings are built from **this project's** scan results "
        "(architecture, security, Compose, quality metrics). "
        "Local AI may polish wording only — it cannot invent unrelated issues."
    )
    if not ai_reviews:
        st.warning("No assessment available. Re-run analysis.")
    elif "error" in ai_reviews and len(ai_reviews) == 1:
        st.error(ai_reviews["error"])
    else:
        for role, text in ai_reviews.items():
            if role == "error":
                st.error(text)
                continue
            with st.expander(role_display_label(role), expanded=True):
                if isinstance(text, str) and (text.startswith("❌") or text.startswith("⏰")):
                    st.error(text)
                else:
                    st.markdown(text)

# ── TAB 6: Auto-Fix ───────────────────────────────────────────
with tab6:
    st.markdown("### 🔧 Auto-Fix System")
    st.caption("Changes are written directly to disk. A backup is created before every change.")

    if not run_auto_fix:
        st.info("Auto-Fix is disabled. Enable it in the sidebar and re-run.")
    elif not fixes_list:
        st.success("✅ No fixable issues found in this project.")
    else:
        fixer = AutoFixEngine(project_path=_project_path)

        total = len(fixes_list)
        applied = len(st.session_state.applied_fixes)
        remaining = total - applied

        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Total Fixes", total)
        c2.metric("✅ Applied", applied)
        c3.metric("🔧 Remaining", remaining)

        if remaining == 0:
            st.success("🎉 All fixes applied!")
            st.balloons()

        st.divider()
        st.markdown("### 📝 Fix List")

        for i, fix in enumerate(fixes_list):
            is_applied = i in st.session_state.applied_fixes
            icon = "✅" if is_applied else "🔧"
            issue_type = fix.get("issue_type", "unknown")
            file_path = fix.get("file", "")
            file_name = os.path.basename(file_path)

            with st.expander(
                    f"{icon} Fix #{i + 1} [{issue_type}] — {fix.get('description', '')[:55]}...",
                    expanded=(not is_applied and i < 3)
            ):
                st.write(f"**File:** `{file_name}`")
                st.write(f"**Path:** `{file_path}`")
                st.write(f"**Confidence:** {fix.get('confidence', 0)}%")
                if fix.get("requires_review"):
                    st.warning("⚠️ Requires manual review before applying.")

                if is_applied:
                    st.success("✅ Already applied in this session.")
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**🔴 Before**")
                        st.code(fix.get("original", ""), language="kotlin")
                    with c2:
                        st.markdown("**🟢 After**")
                        st.code(fix.get("suggested", ""), language="kotlin")

                    if st.button("✅ Apply This Fix", key=f"fix_{i}_{issue_type}"):
                        with st.spinner(f"Writing to {file_name}..."):
                            ok, msg = fixer.apply_fix_direct(
                                file_path,
                                fix.get("original", ""),
                                fix.get("suggested", ""),
                                line_number=fix.get("line_number")
                            )
                        if ok:
                            st.session_state.applied_fixes.add(i)
                            st.success(msg)
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    updated = f.read()
                                with st.expander("📝 Verify — updated file"):
                                    st.code(updated[:800], language="kotlin")
                            except Exception:
                                pass
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        # Batch apply
        pending = [i for i in range(len(fixes_list)) if i not in st.session_state.applied_fixes]
        if pending:
            st.divider()
            st.markdown("### 🚀 Batch Apply")
            if st.button(
                    f"✅ Apply All {len(pending)} Remaining Fixes",
                    type="primary",
                    key="batch_apply"
            ):
                prog = st.progress(0)
                failed = []
                for n, i in enumerate(pending):
                    fix = fixes_list[i]
                    prog.progress((n + 1) / len(pending))
                    ok, msg = fixer.apply_fix_direct(
                        fix["file"],
                        fix.get("original", ""),
                        fix.get("suggested", ""),
                        line_number=fix.get("line_number")
                    )
                    if ok:
                        st.session_state.applied_fixes.add(i)
                    else:
                        failed.append({"desc": fix.get("description", ""), "error": msg})
                prog.empty()
                applied_now = len(pending) - len(failed)
                if applied_now:
                    st.success(f"✅ Applied {applied_now} fixes. Backups in `{fixer.backup_dir}/`")
                if failed:
                    with st.expander("❌ Failed fixes"):
                        for f in failed:
                            st.write(f"• {f['desc']}: {f['error']}")
                st.rerun()

        # Undo
        st.divider()
        if st.button("↩️ Undo Last Fix", key="undo_fix"):
            ok, msg = fixer.undo_last_fix()
            if ok:
                if st.session_state.applied_fixes:
                    st.session_state.applied_fixes.discard(
                        max(st.session_state.applied_fixes)
                    )
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()

# ── TAB 7: Export ─────────────────────────────────────────────
with tab7:
    st.markdown("### 📄 Export Report")
    st.caption(
        "Download a shareable HTML report of this analysis. "
        "PDF export is available if WeasyPrint is installed."
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    html = generate_html_report(
        _project_path,
        health,
        analysis,
        rules,
        vulns,
        ai_reviews,
        technologies=technologies,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇ Download HTML Report",
            data=html.encode("utf-8"),
            file_name=f"appforge_report_{stamp}.html",
            mime="text/html",
            use_container_width=True,
            type="primary",
        )
    with c2:
        pdf_bytes, pdf_err = generate_pdf_bytes(html)
        if pdf_bytes:
            st.download_button(
                "⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=f"appforge_report_{stamp}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button(
                "⬇ Download PDF Report",
                disabled=True,
                use_container_width=True,
                help=pdf_err or "PDF unavailable",
            )
            if pdf_err:
                st.caption(pdf_err)

    with st.expander("👁 Preview report", expanded=False):
        st.components.v1.html(html, height=600, scrolling=True)

st.markdown("---")
st.caption(
    "🛠️ **AppForge ** · Android Code Intelligence · "
    "🧠 Multi-Model AI · 🔒  Zero cloud · 🧠 Three AI models · © 2026"
)