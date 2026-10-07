from collections import Counter
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

def parse_report(path):
    tree = ET.parse(path)
    root = tree.getroot()

    results = Counter()
    failed_rules = []

    for rule in root.findall(".//{*}rule-result"):
        result = rule.find("{*}result")

        if result is None or result.text is None:
            continue

        status = result.text.strip()
        results[status] += 1

        if status == "fail":
            rule_id = rule.get("idref", "unknown")
            rule_id = rule_id.replace(
                "xccdf_org.ssgproject.content_rule_",
                ""
            )
            failed_rules.append(rule_id)

    score_element = root.find(".//{*}score")

    score = None

    if score_element is not None and score_element.text:
        score = float(score_element.text)

    return results, failed_rules, score


def main():
    report_dir = Path(
        sys.argv[1] if len(sys.argv) > 1
        else "reports/before"
    )
    SUMMARY_FILE = report_dir / "summary.md"

    xml_files = sorted(report_dir.glob("*.xml"))

    if not xml_files:
        print(f"No XML reports found in {report_dir}")
        sys.exit(1)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as file:
        file.write("# OpenSCAP CIS Baseline Summary\n\n")

        for xml_file in xml_files:
            results, failed_rules, score = parse_report(xml_file)

            passed = results["pass"]
            failed = results["fail"]

            tested = passed + failed

            pass_rate = (
                passed / tested * 100
                if tested > 0
                else 0
            )
            with open(SUMMARY_FILE, "a", encoding="utf-8") as file:
                print(f"## {xml_file.stem}", file=file)
                print(file=file)
                print(f"- OpenSCAP score: {score}", file=file)
                print(f"- PASS: {passed}", file=file)
                print(f"- FAIL: {failed}", file=file)
                print(f"- NOT APPLICABLE: {results['notapplicable']}", file=file)
                print(f"- PASS RATE: {pass_rate:.1f}%", file=file)
                print(file=file)

                print("### First failed rules", file=file)
                print(file=file)

                for rule in failed_rules[:15]:
                    print(f"- `{rule}`", file=file)

                print(file=file)

if __name__ == "__main__":
    main()

