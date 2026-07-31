import streamlit as st
import plotly.graph_objects as go
from backend.services.scanner import scan_project
from backend.services.rules_engine import analyze_rules
from backend.services.analyzer import detect_duplicates, analyze_compose, detect_technologies
from backend.services.vulnerability import scan_vulnerabilities
from backend.services.health_score import calculate_health_score
from backend.services.ai_reviewer import review_project
from backend.services.report import generate_html_report, save_pdf
from backend.services.cache import make_project_hash, load_cache, save_cache, clear_cache
import os

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
    if st.button("🗑 Clear Cache"):
        clear_cache()
        st.success("Cache cleared")

project_path = st.text_input("Android Project Path", "/path/to/your/android/project")

if st.button("🚀 Analyze Project", type="primary"):
    progress = st.progress(0, text="Starting...")

    try:
        # Step 1: Scan
        progress.progress(10, "Scanning project tree...")
        project = scan_project(project_path)
        kt_count = len(project["kotlin_files"])

        if kt_count == 0:
            st.error("No Kotlin/Java files found. Check the path.")
            st.stop()

        cache_key = make_project_hash(project)

        # Check cache
        cached = load_cache(cache_key) if use_cache else None
        if cached:
            st.info("⚡ Loaded from cache — change a file to trigger a fresh analysis.")
            rules = cached["rules"]
            analysis = cached["analysis"]
            vulns = cached["vulns"]
            health = cached["health"]
            ai_reviews = cached.get("ai_reviews", {})
        else:
            # Step 2: Rules engine
            progress.progress(25, "Running rules engine...")
            rules = analyze_rules(project["files"])

            # Step 3: Advanced analysis
            progress.progress(40, "Analyzing architecture & patterns...")
            duplicates = detect_duplicates(project["files"])
            compose_issues = analyze_compose(project["files"])

            # Detect technologies
            gradle_text = "\n".join(project["gradle_files"]) + "\n" + project["toml"]
            technologies = detect_technologies(gradle_text)

            # Count metrics
            kotlin_files = activities = fragments = services = receivers = 0
            compose = viewmodels = repositories = tests = use_cases = 0

            for file in project["files"]:
                if file["type"] not in ["kotlin", "java"]:
                    continue

                kotlin_files += 1
                code = file["content"]
                name = file["name"].lower()

                if "activity" in name or "Activity" in code: activities += 1
                if "fragment" in name or "Fragment" in code: fragments += 1
                if "service" in name: services += 1
                if "receiver" in name: receivers += 1
                if "viewmodel" in name or "ViewModel" in code: viewmodels += 1
                if "repository" in name or "Repository" in code: repositories += 1
                if "usecase" in name or "UseCase" in code: use_cases += 1
                if "@Composable" in code: compose += code.count("@Composable")
                if "@Test" in code or "@test" in code.lower(): tests += 1

            # Architecture pattern detection
            if use_cases > 0 and repositories > 0:
                arch_pattern = "Clean Architecture"
            elif viewmodels > 0 and repositories > 0:
                arch_pattern = "MVVM"
            elif viewmodels > 0:
                arch_pattern = "MVVM (partial — no Repository layer)"
            elif fragments > 0:
                arch_pattern = "MVP (possible)"
            else:
                arch_pattern = "Unknown / No clear pattern"

            # Git hotspots
            git_stats = project.get("git", {}).get("file_stats", {})
            hotspots = sorted(
                [{"file": k, **v} for k, v in git_stats.items()],
                key=lambda x: x["commits"],
                reverse=True
            )[:5]

            # Recommendations
            recommendations = []
            if viewmodels == 0: recommendations.append("⚠ No ViewModel detected.")
            if repositories == 0: recommendations.append("⚠ No Repository layer detected.")
            if use_cases == 0: recommendations.append("⚠ No UseCase layer — consider Clean Architecture.")
            if not technologies.get("Hilt"): recommendations.append("⚠ Hilt DI not detected.")
            if not technologies.get("Coroutines"): recommendations.append("⚠ Kotlin Coroutines not detected.")
            if rules["todos"] > 0: recommendations.append(f"⚠ {rules['todos']} TODO comments found.")
            if rules["printlns"] > 0: recommendations.append(f"⚠ {rules['printlns']} println() calls found.")
            if rules["http_urls"] > 0: recommendations.append("🚨 HTTP (non-HTTPS) URLs detected.")
            if rules["api_keys"] > 0: recommendations.append("🚨 Possible API key found in source.")
            if len(duplicates) > 3: recommendations.append(f"⚠ {len(duplicates)} duplicate code blocks detected.")
            if rules["null_assertions"] > 5: recommendations.append(
                f"⚠ {rules['null_assertions']} !! null assertions — risky.")
            if len(rules["deprecated_apis"]) > 0:
                names = set(d["api"] for d in rules["deprecated_apis"])
                recommendations.append(f"⚠ Deprecated APIs: {', '.join(names)}")

            analysis = {
                "kotlin_files": kotlin_files,
                "activities": activities,
                "fragments": fragments,
                "services": services,
                "receivers": receivers,
                "compose": compose,
                "viewmodels": viewmodels,
                "repositories": repositories,
                "use_cases": use_cases,
                "tests": tests,
                "technologies": technologies,
                "arch_pattern": arch_pattern,
                "recommendations": recommendations,
                "duplicates": duplicates,
                "compose_issues": compose_issues,
                "git": project.get("git", {}),
                "hotspots": hotspots,
                "total_lines": sum(f["lines"] for f in project["files"])
            }

            # Step 4: CVEs
            if run_vulns:
                progress.progress(55, "Scanning dependencies for CVEs...")
                vulns = scan_vulnerabilities(project["gradle_files"], project["toml"])
            else:
                vulns = {"dependencies": [], "vulnerabilities": [], "scanned": 0}

            # Step 5: Health score
            progress.progress(65, "Computing health score...")
            health = calculate_health_score(analysis, rules, vulns)

            # Step 6: AI Review
            ai_reviews = {}
            if run_ai:
                progress.progress(72, "Running 3 AI models in parallel (this takes ~30–60s)...")
                summary = f"""
Architecture Pattern : {analysis['arch_pattern']}
Kotlin Files : {analysis['kotlin_files']}  |  Total Lines : {analysis['total_lines']}
ViewModels : {analysis['viewmodels']}  |  Repositories : {analysis['repositories']}  |  UseCases : {analysis['use_cases']}
Composable Functions : {analysis['compose']}  |  Tests : {analysis['tests']}
Technologies : {', '.join(k for k, v in analysis['technologies'].items() if v)}
Missing : {', '.join(k for k, v in analysis['technologies'].items() if not v)}
TODOs : {rules['todos']}  |  FIXMEs : {rules['fixmes']}  |  println() : {rules['printlns']}
Null assertions (!!) : {rules['null_assertions']}  |  Large files : {rules['large_files']}
Deprecated APIs : {', '.join(set(d['api'] for d in rules['deprecated_apis'])) or 'None'}
HTTP URLs : {rules['http_urls']}  |  API Keys : {rules['api_keys']}
CVEs found : {len(vulns['vulnerabilities'])}
Compose issues : {len(analysis['compose_issues'])}
Duplicate code blocks : {len(analysis['duplicates'])}
Health Score : {health['overall']}/100
Category scores : {health['categories']}
Recommendations : {chr(10).join(analysis['recommendations'])}
"""
                ai_reviews = review_project(summary)

            # Cache it
            if use_cache:
                save_cache(cache_key, {
                    "rules": rules, "analysis": analysis,
                    "vulns": vulns, "health": health, "ai_reviews": ai_reviews
                })

        progress.progress(100, "Done!")
        progress.empty()

        # ─────────────────────────────────────
        # DISPLAY RESULTS
        # ─────────────────────────────────────

        # Score Header
        score = health["overall"]
        if score >= 80:
            st.success(f"🟢 Overall Health Score: {score}/100")
        elif score >= 60:
            st.warning(f"🟡 Overall Health Score: {score}/100")
        else:
            st.error(f"🔴 Overall Health Score: {score}/100")

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview", "🏗 Architecture", "🛡 Security & CVEs",
            "🎨 Compose", "🤖 AI Review", "📄 Export"
        ])

        # ── TAB 1: Overview ──────────────────
        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Kotlin Files", analysis["kotlin_files"])
            col2.metric("Total Lines", f"{analysis['total_lines']:,}")
            col3.metric("Tests", analysis["tests"])
            col4.metric("Git Commits", project["git"].get("total_commits", "N/A"))

            st.divider()

            # Category radar chart
            cats = health["categories"]
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
            for i, (tech, found) in enumerate(analysis["technologies"].items()):
                cols[i % 4].success(f"✅ {tech}") if found else cols[i % 4].error(f"❌ {tech}")

            st.divider()
            if analysis["recommendations"]:
                st.subheader("📌 Recommendations")
                for r in analysis["recommendations"]:
                    st.warning(r)

            # Git hotspots
            if analysis["hotspots"]:
                st.subheader("🔥 Git Hotspot Files")
                for h in analysis["hotspots"]:
                    st.text(f"{h['commits']:>4} commits — {h['file']}")

        # ── TAB 2: Architecture ──────────────
        with tab2:
            st.subheader(f"Detected Pattern: `{analysis['arch_pattern']}`")
            col1, col2, col3 = st.columns(3)
            col1.metric("ViewModels", analysis["viewmodels"])
            col2.metric("Repositories", analysis["repositories"])
            col3.metric("Use Cases", analysis["use_cases"])

            st.divider()
            st.subheader("📑 Code Duplication")
            if analysis["duplicates"]:
                for d in analysis["duplicates"]:
                    with st.expander(f"{d['file_a']} ↔ {d['file_b']}"):
                        st.code(d["preview"], language="kotlin")
                        st.caption(f"Line {d['line_a']} ↔ Line {d['line_b']}")
            else:
                st.success("No significant duplication detected.")

            st.divider()
            st.subheader("⚠ Deprecated APIs")
            if rules["deprecated_apis"]:
                for d in rules["deprecated_apis"]:
                    st.error(f"`{d['api']}` in **{d['file']}**")
            else:
                st.success("No deprecated API usage found.")

            st.divider()
            st.subheader("📏 Complex Files")
            if rules["complex_files"]:
                for f in sorted(rules["complex_files"], key=lambda x: -x["complexity"]):
                    st.warning(f"**{f['file']}** — complexity score {f['complexity']}")
            else:
                st.success("No high-complexity files found.")

        # ── TAB 3: Security & CVEs ───────────
        with tab3:
            col1, col2, col3 = st.columns(3)
            col1.metric("CVEs Found", len(vulns["vulnerabilities"]))
            col2.metric("Dependencies Scanned", vulns["scanned"])
            col3.metric("Leaked Secrets", rules["api_keys"])

            st.divider()
            st.subheader("🔍 CVE Findings")
            if vulns["vulnerabilities"]:
                for v in vulns["vulnerabilities"]:
                    sev = v.get("severity", "UNKNOWN")
                    with st.expander(f"🚨 {v['cve']} — {v['dependency']}"):
                        st.write(v["description"])
                        st.caption(f"Severity: {sev} · Source: {v.get('source', '')}")
            else:
                st.success("No known CVEs found in dependencies.")

            st.divider()
            st.subheader("🔐 Security Issues in Code")
            if rules["security_issues"]:
                for s in rules["security_issues"]:
                    st.error(f"{s['issue']} — **{s['file']}** ({s['count']} occurrence{'s' if s['count'] > 1 else ''})")
            else:
                st.success("No hardcoded secrets or security patterns found.")

            col1, col2 = st.columns(2)
            col1.metric("HTTP (non-HTTPS) URLs", rules["http_urls"])
            col2.metric("Null assertions (!!)", rules["null_assertions"])

        # ── TAB 4: Compose ───────────────────
        with tab4:
            st.subheader(f"@Composable functions: {analysis['compose']}")
            if analysis["compose_issues"]:
                errors = [i for i in analysis["compose_issues"] if i["severity"] == "error"]
                warnings = [i for i in analysis["compose_issues"] if i["severity"] == "warning"]
                infos = [i for i in analysis["compose_issues"] if i["severity"] == "info"]

                for i in errors:
                    st.error(f"**{i['file']}** — {i['issue']}")
                for i in warnings:
                    st.warning(f"**{i['file']}** — {i['issue']}")
                for i in infos:
                    st.info(f"**{i['file']}** — {i['issue']}")
            else:
                st.success("No Compose recomposition issues detected.")

        # ── TAB 5: AI Review ─────────────────
        with tab5:
            if not ai_reviews:
                st.info("AI Review was disabled. Toggle it in the sidebar and re-run.")
            else:
                labels = {
                    "architecture": "🏗 Architecture Review · llama3.2:3b",
                    "security": "🛡 Security Review · qwen2.5-coder:3b",
                    "performance": "⚡ Performance Review · gemma2:2b"
                }
                for role, text in ai_reviews.items():
                    with st.expander(labels.get(role, role), expanded=True):
                        st.markdown(text)

        # ── TAB 6: Export ────────────────────
        with tab6:
            st.subheader("📤 Export Report")

            html = generate_html_report(
                project_path, health, analysis, rules, vulns, ai_reviews
            )

            st.download_button(
                "⬇ Download HTML Report",
                data=html,
                file_name="android_intelligence_report.html",
                mime="text/html"
            )

            if st.button("📄 Generate PDF"):
                path = save_pdf(html, "aia_report.pdf")
                if path:
                    with open(path, "rb") as f:
                        st.download_button(
                            "⬇ Download PDF",
                            data=f,
                            file_name="android_intelligence_report.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.warning("WeasyPrint not installed. Run `pip install weasyprint` to enable PDF export.")

    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        st.stop()

# Footer
st.markdown("---")
st.caption("🤖 Powered by Multi-Model AI Consensus · Privacy First - All Analysis Runs Locally")