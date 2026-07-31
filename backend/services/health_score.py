def calculate_health_score(analysis, rules, vulns):
    categories = {
        "Architecture": 100,
        "Code Quality": 100,
        "Security": 100,
        "Testing": 100,
        "Performance": 100,
    }

    if analysis["viewmodels"] == 0: categories["Architecture"] -= 25
    if analysis["repositories"] == 0: categories["Architecture"] -= 20
    if not analysis["technologies"].get("Hilt"): categories["Architecture"] -= 10

    categories["Code Quality"] -= rules["todos"] * 2
    categories["Code Quality"] -= rules["fixmes"] * 3
    categories["Code Quality"] -= rules["printlns"] * 4
    categories["Code Quality"] -= rules["null_assertions"] * 2
    categories["Code Quality"] -= len(rules["deprecated_apis"]) * 5

    categories["Security"] -= rules["api_keys"] * 30
    categories["Security"] -= rules["http_urls"] * 10
    categories["Security"] -= len(vulns.get("vulnerabilities", [])) * 8

    if analysis["tests"] == 0:
        categories["Testing"] -= 50
    elif analysis["tests"] < 3:
        categories["Testing"] -= 25

    for k in categories:
        categories[k] = max(0, min(100, int(categories[k])))

    overall = int(sum(categories.values()) / len(categories))
    return {"overall": overall, "categories": categories}