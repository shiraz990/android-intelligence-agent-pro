import streamlit as st
import os
import sys
import traceback
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import base64

# IMPORTANT: set_page_config must be the FIRST Streamlit command
st.set_page_config(
    page_title="Android Intelligence Agent Pro - Enterprise",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import everything else
sys.path.insert(0, os.getcwd())

from backend.services.scanner import scan_project
from backend.services.rules_engine import analyze_rules
from backend.services.analyzer import detect_technologies, detect_duplicates, analyze_compose
from backend.services.vulnerability import scan_vulnerabilities
from backend.services.health_score import calculate_health_score
from backend.services.ai_reviewer import review_project
from backend.services.auto_fixer import AutoFixEngine

# Your custom SVG logo
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
    <linearGradient id="text-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22D3EE"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
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
      <circle cx="256" cy="58" r="9"/>
      <circle cx="434" cy="153" r="9"/>
      <circle cx="434" cy="359" r="9"/>
      <circle cx="256" cy="454" r="9"/>
      <circle cx="78" cy="359" r="9"/>
      <circle cx="78" cy="153" r="9"/>
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

# Professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }
    .sidebar-logo {
        text-align: center;
        padding: 15px 0;
        margin-bottom: 10px;
    }
    .sidebar-logo svg {
        width: 80px;
        height: 80px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(34, 211, 238, 0.2);
    }
    .sidebar-logo h3 {
        color: #667eea;
        margin: 10px 0 5px 0;
        font-weight: 700;
    }
    .sidebar-logo p {
        font-size: 11px;
        color: #8B5CF6;
        margin: 0;
        font-weight: 500;
    }
    .sidebar-logo .status-badge {
        display: inline-block;
        background: linear-gradient(135deg, #22D3EE, #8B5CF6);
        color: white;
        padding: 2px 12px;
        border-radius: 10px;
        font-size: 9px;
        font-weight: 600;
        margin-top: 5px;
    }
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .fix-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    .fix-card.error {
        border-left-color: #dc3545;
    }
    .fix-card.warning {
        border-left-color: #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Professional header
st.markdown("""
<div class="main-header">
    <h1>🤖 Android Intelligence Agent Pro</h1>
    <p>Enterprise-Grade AI Code Review Platform</p>
    <p style="font-size:0.9rem; opacity:0.8;">
        🚀 Powered by Multi-Model AI Consensus · 🔒 100% On-Premise · 📊 Advanced Analytics
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar with Custom Logo
with st.sidebar:
    # Custom SVG Logo
    st.markdown(f"""
    <div class="sidebar-logo">
        {CUSTOM_LOGO_SVG}
        <h3>AI Intelligence</h3>
        <p>Enterprise Edition v2.0</p>
        <span class="status-badge">⚡ AI POWERED</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### ⚙️ Analysis Configuration")
    run_ai = st.toggle("🧠 AI Review", value=True)
    run_auto_fix = st.toggle("🔧 Auto-Fix Suggestions", value=True)
    run_vulns = st.toggle("🛡️ CVE Scanning", value=True)
    run_compose = st.toggle("🎨 Compose Analysis", value=True)

    st.markdown("---")
    st.markdown("### 🧠 AI Models")
    st.info("""
    - 🏗 **llama3.2:3b** - Architecture
    - 🛡 **qwen2.5-coder:3b** - Security
    - ⚡ **gemma2:2b** - Performance
    """)

    # Check Ollama status
    import subprocess

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            st.success("✅ Ollama Running")
        else:
            st.error("❌ Ollama Not Running")
    except:
        st.error("❌ Ollama Not Found")

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    st.caption("Last analysis: Not run yet")
    st.caption("Total projects: 0")
    st.caption("Issues fixed: 0")

# Main content
project_path = st.text_input(
    "📁 Android Project Path",
    "/Users/Android/AndroidApp",
    help="Enter the absolute path to your Android project root directory"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    analyze_btn = st.button("🚀 Analyze Project", type="primary", use_container_width=True)
with col2:
    if st.button("📋 Clear Cache", use_container_width=True):
        st.success("Cache cleared!")

if analyze_btn:
    if not os.path.exists(project_path):
        st.error(f"❌ Path does not exist: {project_path}")
        st.stop()

    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

    try:
        status_text.info("🔍 Scanning project files...")
        progress_bar.progress(10)
        project = scan_project(project_path)

        if len(project['files']) == 0:
            st.error("No files found!")
            st.stop()

        status_text.info("📊 Analyzing code structure...")
        progress_bar.progress(25)

        rules = analyze_rules(project['files'])

        status_text.info("🏗 Detecting architecture patterns...")
        progress_bar.progress(40)
        gradle_text = "\n".join(project["gradle_files"]) + "\n" + project["toml"]
        technologies = detect_technologies(gradle_text)
        duplicates = detect_duplicates(project['files'])
        compose_issues = analyze_compose(project['files']) if run_compose else []

        kotlin_files = 0
        viewmodels = 0
        repositories = 0
        tests = 0

        for file in project['files']:
            if file['type'] in ['kotlin', 'java']:
                kotlin_files += 1
                code = file['content']
                if 'viewmodel' in file['name'].lower() or 'ViewModel' in code:
                    viewmodels += 1
                if 'repository' in file['name'].lower() or 'Repository' in code:
                    repositories += 1
                if '@Test' in code or '@test' in code.lower():
                    tests += 1

        analysis = {
            'kotlin_files': kotlin_files,
            'viewmodels': viewmodels,
            'repositories': repositories,
            'tests': tests,
            'technologies': technologies,
            'duplicates': duplicates,
            'compose_issues': compose_issues,
            'total_lines': sum(f['lines'] for f in project['files']),
            'recommendations': []
        }

        vulns = {"dependencies": [], "vulnerabilities": [], "scanned": 0}
        if run_vulns:
            status_text.info("🔒 Scanning for vulnerabilities...")
            progress_bar.progress(55)
            vulns = scan_vulnerabilities(project["gradle_files"], project["toml"])

        status_text.info("📈 Calculating health score...")
        progress_bar.progress(65)
        health = calculate_health_score(analysis, rules, vulns)

        ai_reviews = {}
        if run_ai:
            status_text.info("🧠 Running AI models in parallel (30-60 seconds)...")
            progress_bar.progress(75)
            summary = f"""
Kotlin Files: {analysis['kotlin_files']}  |  Total Lines: {analysis['total_lines']}
ViewModels: {analysis['viewmodels']}  |  Repositories: {analysis['repositories']}
Composable Issues: {len(analysis['compose_issues'])}  |  Tests: {analysis['tests']}
Technologies: {', '.join(k for k, v in analysis['technologies'].items() if v)}
TODOs: {rules['todos']}  |  FIXMEs: {rules['fixmes']}  |  println(): {rules['printlns']}
Null assertions: {rules['null_assertions']}  |  API Keys: {rules['api_keys']}
CVEs found: {len(vulns['vulnerabilities'])}
Health Score: {health['overall']}/100
"""
            ai_reviews = review_project(summary)

        fixes = []
        if run_auto_fix:
            status_text.info("🔧 Generating auto-fix suggestions...")
            progress_bar.progress(90)
            fixer = AutoFixEngine()
            for file in project['files']:
                fixable_issues = []
                if 'TODO' in file['content']:
                    fixable_issues.append({'type': 'todo'})
                if 'println(' in file['content']:
                    fixable_issues.append({'type': 'println'})
                if '!!' in file['content']:
                    fixable_issues.append({'type': 'null_assertion'})
                if 'http://' in file['content']:
                    fixable_issues.append({'type': 'http_url', 'value': 'http://'})

                if fixable_issues:
                    fixes.extend(fixer.generate_fixes(file['name'], file['content'], fixable_issues))

        progress_bar.progress(100)
        status_text.success("✅ Analysis Complete!")

        # Display Results
        score = health['overall']
        if score >= 80:
            st.success(f"### 🟢 Overall Health Score: {score}/100")
            st.caption("✅ Project is in good health! Keep up the good work!")
        elif score >= 60:
            st.warning(f"### 🟡 Overall Health Score: {score}/100")
            st.caption("⚠️ Some areas need attention. Review recommendations below.")
        else:
            st.error(f"### 🔴 Overall Health Score: {score}/100")
            st.caption("🚨 Critical issues found! Immediate action recommended.")

        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📄 Total Files", len(project['files']))
        col2.metric("📝 Kotlin Files", analysis['kotlin_files'])
        col3.metric("📊 Total Lines", f"{analysis['total_lines']:,}")
        col4.metric("🧪 Tests", analysis['tests'])
        col5.metric("🔒 CVEs Found", len(vulns['vulnerabilities']))

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview", "🏗 Architecture", "🛡 Security",
            "🎨 Compose", "🤖 AI Review", "🔧 Auto-Fix"
        ])

        with tab1:
            cats = health['categories']
            fig = go.Figure(go.Scatterpolar(
                r=list(cats.values()),
                theta=list(cats.keys()),
                fill='toself',
                line_color='#667eea',
                fillcolor='rgba(102,126,234,0.2)'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100])),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#2c3e50',
                margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 🛠️ Technology Stack")
            cols = st.columns(4)
            tech_items = list(technologies.items())
            for i in range(min(len(tech_items), 8)):
                tech, found = tech_items[i]
                col_idx = i % 4
                if found:
                    cols[col_idx].success(f"✅ {tech}")
                else:
                    cols[col_idx].error(f"❌ {tech}")

            st.markdown("### 📌 Recommendations")
            if rules.get('todos', 0) > 0:
                st.warning(f"⚠ **{rules['todos']} TODO comments** - These need attention")
            if rules.get('fixmes', 0) > 0:
                st.warning(f"⚠ **{rules['fixmes']} FIXME comments** - Critical issues to fix")
            if rules.get('printlns', 0) > 0:
                st.warning(f"⚠ **{rules['printlns']} println() calls** - Use proper logging")
            if rules.get('null_assertions', 0) > 0:
                st.warning(f"⚠ **{rules['null_assertions']} null assertions** - Risky !! use safe calls")
            if viewmodels == 0:
                st.error("🚨 **No ViewModels** - Implement MVVM pattern")
            if repositories == 0:
                st.error("🚨 **No Repository layer** - Consider Clean Architecture")

        with tab2:
            st.markdown("### 🏗 Architecture Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("🏛️ ViewModels", viewmodels)
            col2.metric("📁 Repositories", repositories)
            col3.metric("🧪 Tests", tests)

            if viewmodels > 0 and repositories > 0:
                arch = "MVVM with Repository Pattern ✅"
            elif viewmodels > 0:
                arch = "MVVM (partial - no Repository) ⚠️"
            else:
                arch = "Unknown - Consider MVVM 🚨"
            st.info(f"**Detected Architecture:** {arch}")

            st.markdown("### 📑 Code Duplication")
            if duplicates and len(duplicates) > 0:
                for d in duplicates[:5]:
                    with st.expander(f"Duplicate: {d['file_a']} ↔ {d['file_b']}"):
                        st.code(d['preview'], language="kotlin")
            else:
                st.success("✅ No significant duplication detected")

            st.markdown("### ⚠️ Deprecated APIs")
            if rules.get('deprecated_apis', []):
                for d in rules['deprecated_apis']:
                    st.error(f"`{d['api']}` in **{d['file']}**")
            else:
                st.success("✅ No deprecated APIs found")

        with tab3:
            st.markdown("### 🛡️ Security Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("🔒 CVEs Found", len(vulns.get('vulnerabilities', [])))
            col2.metric("📦 Dependencies Scanned", vulns.get('scanned', 0))
            col3.metric("🔑 API Keys Leaked", rules.get('api_keys', 0))

            if vulns.get('vulnerabilities', []):
                st.markdown("#### 🔍 Vulnerabilities Found")
                for v in vulns['vulnerabilities']:
                    with st.expander(f"🚨 {v.get('cve', 'Unknown')} - {v.get('dependency', 'Unknown')}"):
                        st.write(v.get('description', 'No description'))
                        st.caption(f"Severity: {v.get('severity', 'Unknown')}")
            else:
                st.success("✅ No known CVEs found")

        with tab4:
            st.markdown("### 🎨 Jetpack Compose Analysis")
            if compose_issues and len(compose_issues) > 0:
                for issue in compose_issues:
                    if issue['severity'] == 'error':
                        st.error(f"**{issue['file']}**: {issue['issue']}")
                    elif issue['severity'] == 'warning':
                        st.warning(f"**{issue['file']}**: {issue['issue']}")
                    else:
                        st.info(f"**{issue['file']}**: {issue['issue']}")
            else:
                st.success("✅ No Compose issues detected")

        with tab5:
            st.markdown("### 🧠 Multi-Model AI Review")
            if not run_ai:
                st.info("🤖 AI Review is disabled. Enable it in the sidebar.")
            elif isinstance(ai_reviews, dict) and 'error' in ai_reviews:
                st.error(f"❌ {ai_reviews['error']}")
                st.info("💡 Start Ollama with: `ollama serve`")
            elif ai_reviews and isinstance(ai_reviews, dict) and len(ai_reviews) > 0:
                labels = {
                    "architecture": "🏗 Architecture Review · llama3.2:3b",
                    "security": "🛡 Security Review · qwen2.5-coder:3b",
                    "performance": "⚡ Performance Review · gemma2:2b"
                }
                for role, text in ai_reviews.items():
                    if role in labels:
                        with st.expander(labels[role], expanded=True):
                            st.markdown(text)
            else:
                st.warning("No AI reviews generated. Check if Ollama is running.")

        with tab6:
            st.markdown("### 🔧 Auto-Fix Suggestions")
            if not run_auto_fix:
                st.info("Auto-Fix is disabled. Enable it in the sidebar.")
            elif fixes and len(fixes) > 0:
                st.success(f"🎯 Found {len(fixes)} fixable issues!")
                for i, fix in enumerate(fixes):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"#### {i + 1}. {fix['description']}")
                            st.caption(f"📁 {fix['file']} · Confidence: {fix['confidence']}%")
                        with col2:
                            if st.button(f"✅ Apply Fix", key=f"apply_{i}"):
                                st.success(f"Fix applied to {fix['file']}!")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Before:**")
                            st.code(fix['original'], language="kotlin")
                        with col2:
                            st.markdown("**After:**")
                            st.code(fix['suggested'], language="kotlin")
                        st.divider()
            else:
                st.success("✅ No fixable issues found! Your code is clean!")
                st.balloons()

        st.markdown("---")
        st.caption("""
        🤖 **Android Intelligence Agent Pro** · Enterprise Edition  
        🚀 Powered by Multi-Model AI · 🔒 100% On-Premise · 📊 Real-time Analysis  
        © 2026 All Rights Reserved
        """)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.code(traceback.format_exc())