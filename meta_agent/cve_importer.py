import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def build_cve_benchmark_from_cvelistv5(cvelist_dir: Path, output_file: Path, max_samples: int = 12) -> Dict[str, Any]:
    """
    Scans the user's local cvelistV5-main directory and extracts official CVE records
    to generate an official benchmark suite.
    """
    if not cvelist_dir.exists():
        logger.warning(f"CVE directory {cvelist_dir} not found.")
        return {}

    cve_files = [f for f in cvelist_dir.glob("**/*.json") if "CVE-" in f.name]
    logger.info(f"Found {len(cve_files)} official CVE records in {cvelist_dir}")

    test_cases = []
    seen_ids = set()

    for f in cve_files:
        if len(test_cases) >= max_samples:
            break
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                meta = data.get("cveMetadata", {})
                cve_id = meta.get("cveId")
                if not cve_id or cve_id in seen_ids:
                    continue

                cna = data.get("containers", {}).get("cna", {})
                descs = cna.get("descriptions", [])
                desc_text = descs[0].get("value") if descs else ""

                if not desc_text or len(desc_text) < 30:
                    continue

                # Classify status & category from official CVE description
                desc_upper = desc_text.upper()

                if "CROSS-SITE SCRIPTING" in desc_upper or "XSS" in desc_upper:
                    category = "Cross-Site Scripting (XSS)"
                    expected_status = "VULNERABLE"
                elif "SQL INJECTION" in desc_upper or "SQL" in desc_upper:
                    category = "SQL Injection (SQLi)"
                    expected_status = "VULNERABLE"
                elif "DIRECTORY TRAVERSAL" in desc_upper or "PATH TRAVERSAL" in desc_upper:
                    category = "Directory Traversal"
                    expected_status = "VULNERABLE"
                elif "BUFFER OVERFLOW" in desc_upper or "HEAP" in desc_upper:
                    category = "Buffer Overflow / Memory Corruption"
                    expected_status = "VULNERABLE"
                elif "REMOTE CODE EXECUTION" in desc_upper or "COMMAND INJECTION" in desc_upper:
                    category = "Remote Code Execution (RCE)"
                    expected_status = "VULNERABLE"
                elif "PATCH" in desc_upper or "SECURITY RELEASE" in desc_upper or "REJECT" in desc_upper:
                    category = "Patched / Resolved Security Advisory"
                    expected_status = "SAFE"
                else:
                    category = "General Vulnerability Disclosure"
                    expected_status = "VULNERABLE"

                seen_ids.add(cve_id)
                test_cases.append({
                    "id": cve_id,
                    "input": f"Official MITRE cve.org Record ({cve_id}):\n{desc_text.strip()}",
                    "expected_status": expected_status,
                    "expected_category": category
                })
        except Exception as e:
            continue

    benchmark_data = {
        "id": "cve_official_mitre",
        "benchmark_name": "Official MITRE CVE Dataset (cvelistV5)",
        "description": f"Real-world Common Vulnerabilities and Exposures (CVE) parsed directly from the local cvelistV5-main repository.",
        "task_description": "Analyze official cve.org technical vulnerability records and classify as SAFE or VULNERABLE.",
        "seed_prompt": "You are a Senior Vulnerability Security Auditor. Review the official cve.org record below and state whether it is SAFE or VULNERABLE.",
        "test_cases": test_cases
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(benchmark_data, out, indent=2)

    logger.info(f"Successfully created official benchmark '{output_file}' with {len(test_cases)} real CVE test cases.")
    return benchmark_data

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    cvelist_path = base_dir / "cvelistV5-main"
    output_path = base_dir / "meta_agent" / "benchmarks" / "cve_official_mitre.json"
    build_cve_benchmark_from_cvelistv5(cvelist_path, output_path)
