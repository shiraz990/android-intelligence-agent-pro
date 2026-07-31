import streamlit as st
import os
import sys
import traceback

# Add current directory to path
sys.path.insert(0, os.getcwd())

st.set_page_config(
    page_title="Android Intelligence Agent Pro",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Android Intelligence Agent Pro")
st.caption("Multi-model AI review · CVE scanner · Compose analysis · Git hotspots")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    use_cache = st.toggle("Cache results", value=True)
    run_ai = st.toggle("Run AI Review", value=True)
    run_vulns = st.toggle("Scan CVEs", value=True)
    st.divider()
    if st.button("🗑 Clear Cache"):
        st.success("Cache cleared (demo)")

project_path = st.text_input(
    "Android Project Path",
    "/Users/Android/AndroidApp"
)

if st.button("🚀 Analyze Project", type="primary"):

    # Check if path exists
    if not os.path.exists(project_path):
        st.error(f"❌ Path does not exist: {project_path}")
        st.stop()

    st.success(f"✅ Path exists: {project_path}")

    # Import scanner here to avoid import issues
    try:
        from backend.services.scanner import scan_project

        st.write("✅ Scanner imported successfully")
    except Exception as e:
        st.error(f"❌ Import error: {e}")
        st.stop()

    # Check for Kotlin/Java files
    kotlin_files = []
    java_files = []

    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".kt"):
                kotlin_files.append(os.path.join(root, file))
            elif file.endswith(".java"):
                java_files.append(os.path.join(root, file))

    st.write(f"📁 Found {len(kotlin_files)} Kotlin files")
    st.write(f"📁 Found {len(java_files)} Java files")

    if len(kotlin_files) == 0 and len(java_files) == 0:
        st.error("❌ No Kotlin or Java files found!")
        st.info("💡 Create a sample file or point to a real Android project")
        st.stop()

    try:
        progress = st.progress(0, text="Starting analysis...")

        # Step 1: Scan
        progress.progress(10, "Scanning project...")
        st.write("📂 Scanning project...")

        # Call the function correctly with parentheses
        project = scan_project(project_path)
        st.write(f"✅ Found {len(project['files'])} files")

        # Step 2: Simple analysis
        progress.progress(40, "Analyzing...")

        # Count metrics
        total_files = len(project['files'])
        kotlin_count = len(project['kotlin_files'])
        java_count = len(project['java_files'])

        # Count TODOs and FIXMEs
        todos = 0
        fixmes = 0
        printlns = 0

        for file in project['files']:
            content = file.get('content', '')
            todos += content.count("TODO")
            fixmes += content.count("FIXME")
            printlns += content.count("println(")

        # Calculate health score (simple version)
        health_score = 100
        health_score -= todos * 2
        health_score -= fixmes * 3
        health_score -= printlns * 4
        health_score = max(0, min(100, health_score))

        progress.progress(100, "Done!")
        progress.empty()

        # Display Results
        if health_score >= 80:
            st.success(f"🟢 Overall Health Score: {health_score}/100")
        elif health_score >= 60:
            st.warning(f"🟡 Overall Health Score: {health_score}/100")
        else:
            st.error(f"🔴 Overall Health Score: {health_score}/100")

        # Show metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", total_files)
        col2.metric("Kotlin Files", kotlin_count)
        col3.metric("Java Files", java_count)
        col4.metric("TODOs", todos)

        col1, col2, col3 = st.columns(3)
        col1.metric("FIXMEs", fixmes)
        col2.metric("println() calls", printlns)
        col3.metric("Health Score", f"{health_score}/100")

        # Show recommendations
        if todos > 0:
            st.warning(f"⚠ Found {todos} TODO comments that need attention")
        if fixmes > 0:
            st.warning(f"⚠ Found {fixmes} FIXME comments that need fixing")
        if printlns > 0:
            st.warning(f"⚠ Found {printlns} println() calls - use proper logging")

        # Show file list
        with st.expander("📄 Files Analyzed"):
            for file in project['files'][:20]:  # Show first 20
                st.write(f"- {file['name']} ({file['type']}, {file['lines']} lines)")
            if len(project['files']) > 20:
                st.write(f"... and {len(project['files']) - 20} more files")

    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        st.code(traceback.format_exc(), language="python")

st.markdown("---")
st.caption("🤖 Android Intelligence Agent · Privacy First - All Analysis Runs Locally")