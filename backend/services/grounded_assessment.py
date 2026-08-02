"""
Project-grounded assessment narratives.

Built only from scan results for the analyzed project — never generic filler.
"""
from typing import Any, Dict, List, Optional


def _arch_label(viewmodels: int, repositories: int) -> str:
    if viewmodels > 0 and repositories > 0:
        return "MVVM with Repository pattern"
    if viewmodels > 0:
        return "MVVM without a clear Repository layer"
    return "no clear MVVM / ViewModel structure"


def _priority(level: str) -> str:
    return {"high": "High", "medium": "Medium", "low": "Low"}.get(level, level.title())


def build_grounded_assessments(
    *,
    project_path: str,
    analysis: Dict[str, Any],
    rules: Dict[str, Any],
    vulns: Dict[str, Any],
    health: Dict[str, Any],
    technologies: Optional[Dict[str, bool]] = None,
    duplicates: Optional[List[Dict]] = None,
    compose_issues: Optional[List[Dict]] = None,
) -> Dict[str, str]:
    """
    Return analyzer / fixer / reviewer markdown grounded in this project's facts.
    """
    technologies = technologies or analysis.get("technologies") or {}
    duplicates = duplicates if duplicates is not None else analysis.get("duplicates") or []
    compose_issues = (
        compose_issues
        if compose_issues is not None
        else analysis.get("compose_issues") or []
    )

    kotlin_files = analysis.get("kotlin_files", 0)
    total_lines = analysis.get("total_lines", 0)
    viewmodels = analysis.get("viewmodels", 0)
    repositories = analysis.get("repositories", 0)
    tests = analysis.get("tests", 0)
    overall = health.get("overall", 0)
    cats = health.get("categories") or {}
    project_name = project_path.rstrip("\\/").split("\\")[-1].split("/")[-1]

    tech_on = [k for k, v in technologies.items() if v]
    tech_off = [k for k, v in technologies.items() if not v]
    arch = _arch_label(viewmodels, repositories)

    return {
        "analyzer": _architecture_section(
            project_name=project_name,
            kotlin_files=kotlin_files,
            total_lines=total_lines,
            viewmodels=viewmodels,
            repositories=repositories,
            tests=tests,
            arch=arch,
            tech_on=tech_on,
            tech_off=tech_off,
            duplicates=duplicates,
            rules=rules,
            overall=overall,
            cats=cats,
        ),
        "fixer": _security_section(
            project_name=project_name,
            rules=rules,
            vulns=vulns or {},
            overall=overall,
            cats=cats,
        ),
        "reviewer": _performance_section(
            project_name=project_name,
            rules=rules,
            compose_issues=compose_issues,
            tests=tests,
            kotlin_files=kotlin_files,
            total_lines=total_lines,
            overall=overall,
            cats=cats,
        ),
    }


def _architecture_section(
    *,
    project_name,
    kotlin_files,
    total_lines,
    viewmodels,
    repositories,
    tests,
    arch,
    tech_on,
    tech_off,
    duplicates,
    rules,
    overall,
    cats,
) -> str:
    findings: List[str] = []
    actions: List[str] = []

    findings.append(
        f"1. **{_priority('medium')} — Architecture shape** — "
        f"`{project_name}` has **{kotlin_files}** Kotlin/Java sources "
        f"(**{total_lines:,}** LOC). Detected structure: **{arch}** "
        f"(ViewModels: **{viewmodels}**, Repositories: **{repositories}**)."
    )
    if viewmodels == 0:
        actions.append(
            "Introduce ViewModel-backed UI state for primary screens to stabilize presentation logic."
        )
    elif repositories == 0:
        actions.append(
            f"Add a Repository layer under the existing {viewmodels} ViewModel(s) "
            "to separate data access from UI state."
        )

    if tests == 0:
        findings.append(
            f"2. **{_priority('high')} — Test coverage gap** — "
            f"No `@Test` usage was detected across {kotlin_files} source files. "
            f"Testing category score: **{cats.get('Testing', 'n/a')}/100**."
        )
        actions.append(
            "Add unit tests for ViewModels/Repositories first; target critical user flows."
        )
    elif tests < 3:
        findings.append(
            f"2. **{_priority('medium')} — Limited tests** — "
            f"Only **{tests}** test signal(s) found. Testing score: "
            f"**{cats.get('Testing', 'n/a')}/100**."
        )
        actions.append(f"Expand automated tests beyond the current {tests} coverage points.")

    deprecated = rules.get("deprecated_apis") or []
    if deprecated:
        samples = ", ".join(
            f"`{d.get('api')}` in `{d.get('file')}`" for d in deprecated[:5]
        )
        findings.append(
            f"3. **{_priority('high')} — Deprecated Android APIs** — "
            f"**{len(deprecated)}** occurrence(s): {samples}."
        )
        actions.append("Replace deprecated APIs with current Jetpack / Activity Result equivalents.")

    if duplicates:
        samples = "; ".join(
            f"`{d.get('file_a')}` L{d.get('line_a')} ↔ `{d.get('file_b')}` L{d.get('line_b')}"
            for d in duplicates[:4]
        )
        findings.append(
            f"4. **{_priority('medium')} — Code duplication** — "
            f"**{len(duplicates)}** similar block(s) detected. Examples: {samples}."
        )
        actions.append("Extract shared helpers for the duplicated blocks listed above.")

    complex_files = rules.get("complex_files") or []
    if complex_files:
        samples = ", ".join(
            f"`{c.get('file')}` (complexity {c.get('complexity')})"
            for c in complex_files[:5]
        )
        findings.append(
            f"5. **{_priority('medium')} — High cyclomatic complexity** — {samples}."
        )
        actions.append(f"Split the highest-complexity file(s): {complex_files[0].get('file')}.")

    large = rules.get("large_files", 0)
    if large:
        findings.append(
            f"6. **{_priority('low')} — Large source files** — "
            f"**{large}** file(s) exceed 300 lines."
        )
        actions.append("Break down files over 300 LOC into focused modules/classes.")

    if tech_on:
        findings.append(
            f"7. **{_priority('low')} — Stack in use** — {', '.join(tech_on)}."
        )
    if tech_off:
        # Only call out high-value absences
        notable = [t for t in tech_off if t in ("Hilt", "Coroutines", "Jetpack Compose", "Room")]
        if notable and viewmodels > 0:
            findings.append(
                f"8. **{_priority('low')} — Stack gaps** — Not detected: {', '.join(notable)}."
            )

    if len(findings) == 1:
        findings.append(
            "2. **Low — Maintainability** — No major duplication, deprecated-API, or complexity "
            "hotspots were flagged beyond the architecture snapshot above."
        )

    if not actions:
        actions.append(
            f"Maintain current architecture practices; re-scan after the next major feature in `{project_name}`."
        )

    arch_score = cats.get("Architecture", "n/a")
    return f"""## Architecture Assessment

### Executive summary
Project **`{project_name}`** scores **{overall}/100** overall (Architecture **{arch_score}/100**).
Static analysis of **{kotlin_files}** sources (**{total_lines:,}** LOC) indicates **{arch}**,
with **{viewmodels}** ViewModel signal(s), **{repositories}** Repository signal(s), and **{tests}** test signal(s).

### Findings
{chr(10).join(findings)}

### Recommended actions
{chr(10).join(f'- {a}' for a in actions[:6])}
"""


def _security_section(*, project_name, rules, vulns, overall, cats) -> str:
    findings: List[str] = []
    actions: List[str] = []
    vuln_list = vulns.get("vulnerabilities") or []
    scanned = vulns.get("scanned", 0)
    sec_score = cats.get("Security", "n/a")

    if vuln_list:
        for i, v in enumerate(vuln_list[:6], 1):
            findings.append(
                f"{i}. **{_priority('high')} — {v.get('cve', 'CVE')}** — "
                f"Dependency `{v.get('dependency', '?')}`: {v.get('description', 'See advisory')}. "
                f"Source: {v.get('source', 'scan')}."
            )
        actions.append(
            "Upgrade or replace the vulnerable dependencies listed above; verify with a dependency lock review."
        )
    else:
        findings.append(
            f"1. **{_priority('low')} — Dependency CVEs** — "
            f"Scanned **{scanned}** coordinated dependencies; **no known CVEs** reported for this project."
        )

    http_urls = rules.get("http_urls", 0)
    if http_urls:
        findings.append(
            f"{len(findings)+1}. **{_priority('high')} — Cleartext HTTP** — "
            f"**{http_urls}** `http://` URL(s) found in source. Prefer HTTPS."
        )
        actions.append(f"Replace all {http_urls} HTTP endpoint(s) with HTTPS and enforce network security config.")

    sec_issues = rules.get("security_issues") or []
    if sec_issues:
        for s in sec_issues[:6]:
            findings.append(
                f"{len(findings)+1}. **{_priority('high')} — {s.get('issue', 'Security pattern')}** — "
                f"File `{s.get('file')}` ({s.get('count', 1)}×)."
            )
        actions.append("Remove hardcoded secrets/keys from source; move credentials to secure storage or CI secrets.")

    nulls = rules.get("null_assertions", 0)
    if nulls:
        findings.append(
            f"{len(findings)+1}. **{_priority('medium')} — Crash risk from `!!`** — "
            f"**{nulls}** non-null assertion(s) can trigger runtime crashes on unexpected nulls."
        )
        actions.append(f"Replace the {nulls} `!!` usage(s) with safe calls / explicit null handling.")

    if len(findings) == 1 and not vuln_list and not http_urls and not sec_issues and not nulls:
        findings.append(
            f"2. **{_priority('low')} — Code security patterns** — "
            f"No hardcoded secret patterns, HTTP URLs, or `!!` crash risks were flagged in `{project_name}`."
        )

    if not actions:
        actions.append(
            f"Keep dependency scanning enabled for `{project_name}` on each release candidate."
        )

    return f"""## Security Assessment

### Executive summary
Security category score for **`{project_name}`**: **{sec_score}/100** (overall health **{overall}/100**).
Dependency scan covered **{scanned}** artifact(s) with **{len(vuln_list)}** CVE finding(s).
Code-pattern scan reported **{http_urls}** HTTP URL(s), **{len(sec_issues)}** secret/weak-crypto hit(s),
and **{nulls}** null-assertion(s).

### Findings
{chr(10).join(findings)}

### Recommended actions
{chr(10).join(f'- {a}' for a in actions[:6])}
"""


def _performance_section(
    *,
    project_name,
    rules,
    compose_issues,
    tests,
    kotlin_files,
    total_lines,
    overall,
    cats,
) -> str:
    findings: List[str] = []
    actions: List[str] = []
    perf_score = cats.get("Performance", "n/a")
    quality_score = cats.get("Code Quality", "n/a")

    printlns = rules.get("printlns", 0)
    logd = rules.get("logd", 0)
    todos = rules.get("todos", 0)
    fixmes = rules.get("fixmes", 0)
    nulls = rules.get("null_assertions", 0)
    large = rules.get("large_files", 0)
    complex_files = rules.get("complex_files") or []

    findings.append(
        f"1. **{_priority('medium')} — Release hygiene baseline** — "
        f"`{project_name}`: **{kotlin_files}** sources / **{total_lines:,}** LOC · "
        f"Performance score **{perf_score}/100** · Code Quality **{quality_score}/100**."
    )

    if printlns:
        findings.append(
            f"2. **{_priority('medium')} — Debug `println` in production paths** — "
            f"**{printlns}** `println()` call(s) can add main-thread I/O noise and leak debug output."
        )
        actions.append(f"Replace {printlns} `println()` call(s) with guarded `Log` statements or remove them.")

    if logd:
        findings.append(
            f"{len(findings)+1}. **{_priority('low')} — Verbose `Log.d`** — "
            f"**{logd}** debug log call(s) present; strip or gate before release builds."
        )
        actions.append(f"Gate or remove {logd} `Log.d` call(s) in release variants.")

    if compose_issues:
        for issue in compose_issues[:5]:
            findings.append(
                f"{len(findings)+1}. **{_priority('high' if issue.get('severity') == 'error' else 'medium')} — "
                f"Compose: {issue.get('issue')}** — File `{issue.get('file')}`."
            )
        actions.append(
            f"Fix Compose recomposition issues in: "
            + ", ".join(f"`{i.get('file')}`" for i in compose_issues[:4])
        )

    if nulls:
        findings.append(
            f"{len(findings)+1}. **{_priority('high')} — Null assertion crash risk** — "
            f"**{nulls}** `!!` usage(s) are stability risks under unexpected null data."
        )
        actions.append(f"Eliminate {nulls} `!!` assertion(s) in hot paths.")

    if complex_files:
        top = complex_files[0]
        findings.append(
            f"{len(findings)+1}. **{_priority('medium')} — Complexity hotspot** — "
            f"`{top.get('file')}` scored complexity **{top.get('complexity')}**; "
            f"**{len(complex_files)}** complex file(s) total."
        )
        actions.append(f"Refactor `{top.get('file')}` to reduce branching and improve maintainability.")

    if large:
        findings.append(
            f"{len(findings)+1}. **{_priority('low')} — Oversized files** — "
            f"**{large}** file(s) > 300 LOC may hurt compile/review throughput."
        )

    if todos or fixmes:
        findings.append(
            f"{len(findings)+1}. **{_priority('medium')} — Unfinished work markers** — "
            f"**{todos}** TODO(s), **{fixmes}** FIXME(s) remain in the tree."
        )
        actions.append(f"Clear {fixmes} FIXME(s) before release; schedule the {todos} TODO(s).")

    if tests == 0:
        findings.append(
            f"{len(findings)+1}. **{_priority('high')} — No automated tests** — "
            "Regressions in performance-sensitive paths will be caught late."
        )
        actions.append("Add smoke/unit tests for critical screens and data layers before the next release.")

    # If project is clean, say so with project numbers — still specific, not generic
    material = printlns or logd or compose_issues or nulls or complex_files or large or todos or fixmes or tests == 0
    if not material:
        findings.append(
            f"2. **{_priority('low')} — No major static performance risks** — "
            f"No `println`/`Log.d` spikes, Compose recomposition issues, `!!` clusters, "
            f"or complexity hotspots were flagged in `{project_name}`."
        )
        actions.append(
            f"Retain current hygiene in `{project_name}`; re-run AppForge after large Compose or networking changes."
        )

    if not actions:
        actions.append(f"Monitor Code Quality (**{quality_score}/100**) on the next `{project_name}` release build.")

    return f"""## Performance & Release Readiness

### Executive summary
Release-readiness for **`{project_name}`** is based on this project's static signals
(logging hygiene, null-safety, Compose correctness, complexity, tests) —
overall health **{overall}/100**, Performance **{perf_score}/100**, Code Quality **{quality_score}/100**.
Observed: **{printlns}** `println`, **{logd}** `Log.d`, **{nulls}** `!!`,
**{len(compose_issues)}** Compose issue(s), **{tests}** test signal(s).

### Findings
{chr(10).join(findings)}

### Recommended actions
{chr(10).join(f'- {a}' for a in actions[:6])}
"""
