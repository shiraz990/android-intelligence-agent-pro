import streamlit as st
import os
import sys
import traceback
import plotly.graph_objects as go

sys.path.insert(0, os.getcwd())

from backend.services.scanner import scan_project
from backend.services.rules_engine import analyze_rules
from backend.services.analyzer import detect_technologies, detect_duplicates, analyze_compose
from backend.services.vulnerability import scan_vulnerabilities
from backend.services.health_score import calculate_health_score
from backend.services.ai_reviewer import review_project

st.set_page_config(
    page_title="Android Intelligence Agent Pro",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Android Intelligence Agent Pro")
st.caption("Multi-model AI review · CVE scanner · Compose analysis · Git hotspots · HTML/PDF export")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    use_cache = st.toggle("Cache results", value=True)
    run_ai = st.toggle("Run AI Review", value=True)
    run_vulns = st.toggle("Scan CVEs", value=True)

    st.divider()
    if run_ai:
        st.info(
            "🧠 **AI Models Used:**\n- 🏗 llama3.2:3b (Architecture)\n- 🛡 qwen2.5-coder:3b (Security)\n- ⚡ gemma2:2b (Performance)")

        # Check Ollama status
        import subprocess

        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                st.success("✅ Ollama is running")
            else:
                st.error("❌ Ollama not running")
        except:
            st.error("❌ Ollama not found")

project_path = st.text_input(
    "Android Project Path",
    "/Users/Android/AndroidApp"
)

if st.button("🚀 Analyze Project", type="primary"):
    if not os.path.exists(project_path):
        st.error(f"❌ Path does not exist: {project_path}")
        st.stop()

    progress = st.progress(0, text="Starting...")

    try:
        # Step 1: Scan
        progress.progress(10, "Scanning project...")
        project = scan_project(project_path)

        if len(project['files']) == 0:
            st.error("No files found!")
            st.stop()

        # Step 2: Rules Engine
        progress.progress(25, "Running rules engine...")
        rules = analyze_rules(project['files'])

        # Step 3: Advanced Analysis
        progress.progress(40, "Analyzing architecture...")
        gradle_text = "\n".join(project["gradle_files"]) + "\n" + project["toml"]
        technologies = detect_technologies(gradle_text)
        duplicates = detect_duplicates(project['files'])
        compose_issues = analyze_compose(project['files'])

        # Count metrics
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

        # Step 4: CVEs
        vulns = {"dependencies": [], "vulnerabilities": [], "scanned": 0}
        if run_vulns:
            progress.progress(55, "Scanning CVEs...")
            vulns = scan_vulnerabilities(project["gradle_files"], project["toml"])

        # Step 5: Health Score
        progress.progress(65, "Calculating health score...")
        health = calculate_health_score(analysis, rules, vulns)

        # Step 6: AI Review (Multi-Model Parallel)
        ai_reviews = {}
        if run_ai:
            progress.progress(75, "Running 3 AI models in parallel...")
            st.info("🧠 AI models are analyzing your code (this takes 30-60 seconds)...")

            # Build summary for AI
            summary = f"""
Architecture Pattern: {analysis.get('arch_pattern', 'Unknown')}
Kotlin Files: {analysis['kotlin_files']}  |  Total Lines: {analysis['total_lines']}
ViewModels: {analysis['viewmodels']}  |  Repositories: {analysis['repositories']}
Composable Functions: {len(analysis['compose_issues'])}  |  Tests: {analysis['tests']}
Technologies: {', '.join(k for k, v in analysis['technologies'].items() if v)}
TODOs: {rules['todos']}  |  FIXMEs: {rules['fixmes']}  |  println(): {rules['printlns']}
Null assertions (!!): {rules['null_assertions']}  |  Large files: {rules['large_files']}
Deprecated APIs: {len(rules['deprecated_apis'])}  |  HTTP URLs: {rules['http_urls']}
API Keys: {rules['api_keys']}  |  CVEs found: {len(vulns['vulnerabilities'])}
Health Score: {health['overall']}/100
Category scores: Architecture:{health['categories']['Architecture']}, Code Quality:{health['categories']['Code Quality']}, Security:{health['categories']['Security']}, Testing:{health['categories']['Testing']}, Performance:{health['categories']['Performance']}
"""
            ai_reviews = review_project(summary)

        progress.progress(100, "Done!")
        progress.empty()

        # ─── DISPLAY RESULTS ───

        # Health Score
        score = health['overall']
        if score >= 80:
            st.success(f"🟢 Overall Health Score: {score}/100")
        elif score >= 60:
            st.warning(f"🟡 Overall Health Score: {score}/100")
        else:
            st.error(f"🔴 Overall Health Score: {score}/100")

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "🏗 Architecture", "🛡 Security & CVEs",
            "🎨 Compose", "🤖 AI Review"
        ])

        # ── TAB 1: Overview ──
        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Files", len(project['files']))
            col2.metric("Kotlin Files", analysis['kotlin_files'])
            col3.metric("Total Lines", f"{analysis['total_lines']:,}")
            col4.metric("Tests", analysis['tests'])

            # Radar Chart
            cats = health['categories']
            fig = go.Figure(go.Scatterpolar(
                r=list(cats.values()),
                theta=list(cats.keys()),
                fill='toself',
                line_color='#6ee7b7',
                fillcolor='rgba(110,231,183,0.2)'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100])),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0',
                margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Technologies
            st.subheader("🛠 Detected Technologies")
            cols = st.columns(4)
            for i, (tech, found) in enumerate(technologies.items()):
                cols[i % 4].success(f"✅ {tech}") if found else cols[i % 4].error(f"❌ {tech}")

            # Recommendations
            st.subheader("📌 Recommendations")
            if rules['todos'] > 0:
                st.warning(f"⚠ {rules['todos']} TODO comments found")
            if rules['fixmes'] > 0:
                st.warning(f"⚠ {rules['fixmes']} FIXME comments found")
            if rules['printlns'] > 0:
                st.warning(f"⚠ {rules['printlns']} println() calls found")
            if rules['null_assertions'] > 0:
                st.warning(f"⚠ {rules['null_assertions']} null assertions (!!) found")
            if viewmodels == 0:
                st.warning("⚠ No ViewModels detected")
            if repositories == 0:
                st.warning("⚠ No Repository layer detected")

        # ── TAB 2: Architecture ──
        with tab2:
            col1, col2, col3 = st.columns(3)
            col1.metric("ViewModels", viewmodels)
            col2.metric("Repositories", repositories)
            col3.metric("Tests", tests)

            st.divider()
            st.subheader("📑 Code Duplication")
            if duplicates:
                for d in duplicates[:5]:
                    st.warning(f"Duplicate found: {d['file_a']} ↔ {d['file_b']}")
                    st.code(d['preview'], language="kotlin")
            else:
                st.success("No significant duplication detected")

            st.divider()
            st.subheader("⚠ Deprecated APIs")
            if rules['deprecated_apis']:
                for d in rules['deprecated_apis']:
                    st.error(f"`{d['api']}` in **{d['file']}**")
            else:
                st.success("No deprecated APIs found")

        # ── TAB 3: Security ──
        with tab3:
            col1, col2, col3 = st.columns(3)
            col1.metric("CVEs Found", len(vulns['vulnerabilities']))
            col2.metric("Dependencies Scanned", vulns['scanned'])
            col3.metric("API Keys Leaked", rules['api_keys'])

            if vulns['vulnerabilities']:
                st.subheader("🔍 Vulnerabilities Found")
                for v in vulns['vulnerabilities']:
                    with st.expander(f"🚨 {v['cve']} - {v['dependency']}"):
                        st.write(v['description'])
                        st.caption(f"Severity: {v.get('severity', 'Unknown')}")
            else:
                st.success("✅ No known CVEs found")

            if rules['security_issues']:
                st.subheader("🔐 Security Issues")
                for s in rules['security_issues']:
                    st.error(f"{s['issue']} in **{s['file']}** ({s['count']} occurrences)")

        # ── TAB 4: Compose ──
        with tab4:
            if compose_issues:
                st.subheader("🎨 Compose Issues Found")
                for issue in compose_issues:
                    if issue['severity'] == 'error':
                        st.error(f"**{issue['file']}**: {issue['issue']}")
                    elif issue['severity'] == 'warning':
                        st.warning(f"**{issue['file']}**: {issue['issue']}")
                    else:
                        st.info(f"**{issue['file']}**: {issue['issue']}")
            else:
                st.success("✅ No Compose issues detected")

        # ── TAB 5: AI Review ──
        with tab5:
            if not run_ai:
                st.info("🤖 AI Review is disabled. Enable it in the sidebar.")
            elif 'error' in ai_reviews:
                st.error(f"❌ {ai_reviews['error']}")
                st.info("💡 Start Ollama with: `ollama serve`")
            elif ai_reviews:
                st.subheader("🧠 Multi-Model AI Review")
                st.caption("3 specialized AI models analyzed your code in parallel")

                # Show results from each model
                labels = {
                    "architecture": "🏗 Architecture Review · llama3.2:3b",
                    "security": "🛡 Security Review · qwen2.5-coder:3b",
                    "performance": "⚡ Performance Review · gemma2:2b"
                }

                for role, text in ai_reviews.items():
                    with st.expander(labels.get(role, role), expanded=True):
                        st.markdown(text)

                # Add summary
                st.divider()
                st.info(
                    "💡 **What this means:** You got feedback from 3 specialized AI models. Use these insights to improve your code quality.")
            else:
                st.warning("No AI reviews generated. Check if Ollama is running.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.code(traceback.format_exc())

st.markdown("---")
st.caption("🤖 Powered by Android Intelligence Agent · Multi-Model AI Consensus")