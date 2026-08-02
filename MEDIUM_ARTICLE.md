# AppForge: Smarter Android Code Reviews — Right on Your Laptop

### AI-powered quality checks for Android apps, without sending your code to the cloud.

---

Android apps get complicated fast.

What starts as a clean project slowly picks up problems: unfinished TODOs, unsafe code, old libraries, missing tests, and architecture that no longer matches the original plan. Most of these issues stay hidden until a release is close — or until something breaks.

Lint tools catch some of it. Cloud AI tools can catch more, but they often require uploading your source code. For many teams, that is not an option.

**AppForge** sits in the middle.

It reviews your Android project on your own machine, explains what needs attention, and helps you improve the code — privately and clearly.

---

## What AppForge Does

AppForge is a local Android code review tool. You give it your project path, click analyze, and it checks your app from several important angles:

- **Architecture** — Is the project structured well (for example, MVVM with repositories)?
- **Code quality** — Are there TODOs, debug prints, risky null checks, or outdated APIs?
- **Security** — Are there secrets in code, unsafe HTTP links, or known library vulnerabilities (CVEs)?
- **Testing** — Does the project have meaningful test coverage?
- **Performance & release readiness** — Is the app in good shape to ship?

At the end, you get a clear **health score**, detailed findings, fix suggestions, and a report you can share with your team.

---

## Why It Runs Locally

AppForge uses local AI models through **Ollama**. Your project stays on your computer.

That matters if you work with:

- Private or client code
- Fintech, healthcare, or regulated products
- Any team that cannot send source code to external AI services

You still get AI-assisted review. You do not give up control of your codebase.

---

## How to Set Up and Run AppForge

You do not need a cloud account. A new user can get started in a few minutes.

### What you need

- Python 3.11 or newer
- Ollama (for local AI models)
- An Android project on your machine to analyze

### Step 1: Install Python

Download Python from [python.org](https://www.python.org/downloads/).

During installation on Windows, check **Add Python to PATH**.

Confirm it works:

```bash
python --version
```

### Step 2: Install Ollama

Download Ollama from [ollama.com](https://ollama.com).

After installing, start it:

```bash
ollama serve
```

### Step 3: Download the AI models

Open a new terminal and pull the three models AppForge uses:

```bash
ollama pull deepseek-coder:1.3b
ollama pull qwen2.5-coder:3b
ollama pull gemma2:2b
```

This is a one-time download. It may take a few minutes depending on your internet speed.

### Step 4: Get the AppForge project

Clone or download the AppForge repository, then open a terminal inside the project folder.

### Step 5: Install Python packages

```bash
pip install streamlit plotly pandas requests
```

Optional (for PDF export):

```bash
pip install weasyprint
```

### Step 6: Launch AppForge

```bash
streamlit run app_professional.py
```

Your browser should open at:

```text
http://localhost:8501
```

If it does not open automatically, paste that link into your browser.

### Step 7: Analyze your Android project

1. In the sidebar, keep the options you want enabled (AI Review, Auto-Fix, CVE Scanning, Compose Analysis).
2. Paste the full path to your Android project.  
   Example (Windows): `C:\Users\yourname\AndroidStudioProjects\MyApp`
3. Click **Analyze Project**.
4. Review the health score, findings, and AI assessments.
5. Apply suggested fixes only after reviewing them.
6. Export an HTML or PDF report if you want to share results.

### Quick tip

Before analyzing, check the sidebar:

- If it says **Ollama Running**, you are ready for AI review.
- If it says **Ollama Not Found**, run `ollama serve` again and refresh the page.

That is the full setup. After the first run, you usually only need Step 2 and Step 6.

---

## The Model Council (In Plain Terms)

Instead of relying on one AI model for everything, AppForge uses three local models with clear roles:

| Focus | Model | What it looks at |
|---|---|---|
| Architecture | deepseek-coder | Structure and long-term maintainability |
| Security | qwen2.5-coder | Risks, secrets, and vulnerability priorities |
| Performance & release | gemma2 | Shipping readiness and performance-related signals |

Importantly, AppForge does not invent findings. It first scans your project for real signals — file counts, architecture patterns, CVEs, code issues — and then uses AI to explain those results in clear language.

So the review stays tied to *your* project, not generic advice.

---

## What You Get After Analysis

### 1. Health score
A simple overall score, plus category scores for architecture, quality, security, testing, and performance.

### 2. Practical findings
Things like:

- Hardcoded API keys or passwords
- `http://` links that should be `https://`
- Risky `!!` null assertions
- Deprecated Android APIs
- Missing ViewModels, repositories, or tests
- Jetpack Compose issues
- Vulnerable dependencies

### 3. Auto-fix suggestions
For common problems, AppForge can suggest fixes. It creates backups before applying changes, so you stay in control.

### 4. Shareable reports
Export HTML or PDF summaries for pull requests, sprint reviews, audits, or stakeholder updates.

---

## Who It Helps

**Developers** get faster feedback before a PR.  
**Tech leads** get a shared picture of project health.  
**Security teams** get useful checks without moving code off-device.  
**Managers** get clear reports instead of vague “the code feels messy” conversations.

---

## The Idea Behind AppForge

Good Android quality should be easy to see and easy to act on.

AppForge is built around three simple rules:

1. **Keep code local**
2. **Base findings on real project evidence**
3. **Make results easy to understand and fix**

It does not replace Android Studio, CI, or human review. It makes those workflows stronger.

---

## Final Thought

If you have ever opened an Android project and wondered,  
“Is this actually ready to ship — and can we check that without uploading our code?”  

AppForge is built to answer that.

Forge better Android code. Keep it private. Ship with more confidence.

---

## About AppForge

**AppForge** is a privacy-first Android intelligence tool for local code review, security checks, Compose analysis, AI assessments, auto-fix suggestions, and professional reporting.

**Edition:** Core v1.0  
**Runs on:** Your machine (with Ollama)  
**Focus:** Architecture · Security · Performance · Release readiness

---

### Suggested Medium tags
`Android` · `Kotlin` · `Software Engineering` · `AI` · `Code Quality` · `Mobile Development` · `DevSecOps` · `Privacy`

### Suggested titles
1. **AppForge: AI Android Code Review That Stays on Your Laptop**  
2. **Better Android Reviews Without Sending Code to the Cloud**  
3. **A Simple Local Tool for Android Quality, Security, and Release Readiness**
