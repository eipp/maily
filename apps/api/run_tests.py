#!/usr/bin/env python3
"""
Test runner script for campaign API tests.

This script runs all campaign API tests, generates a coverage report,
and provides a summary of passing and failing tests with recommendations.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple, Any


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run campaign API tests")
    parser.add_argument(
        "--implementation",
        choices=["fixed", "router", "both"],
        default="both",
        help="Implementation to test (fixed, router, or both)"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--output",
        help="Output file for report (defaults to test_report_{timestamp}.json)"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report"
    )
    return parser.parse_args()


def run_tests(implementation: str, verbose: bool = False, coverage: bool = False) -> Tuple[int, Dict[str, Any]]:
    """Run tests for specified implementation.

    Args:
        implementation: Implementation to test (fixed, router, or both)
        verbose: Whether to show verbose output
        coverage: Whether to generate coverage report

    Returns:
        Tuple of (exit code, test results)
    """
    print(f"\n--- Running tests for {implementation} implementation ---\n")

    # Prepare command
    cmd = ["pytest"]

    # Add test paths based on implementation
    if implementation == "fixed":
        cmd.append("apps/api/fixed_tests/")
    elif implementation == "router":
        cmd.append("apps/api/tests/integration/")
    else:  # both
        cmd.extend([
            "apps/api/fixed_tests/",
            "apps/api/tests/integration/"
        ])

    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")

    # Add coverage options if requested
    if coverage:
        cmd.extend([
            "--cov=apps.api",
            "--cov-report=term",
            "--cov-report=json:coverage.json"
        ])

    # Add JUnit XML output for parsing
    cmd.append("--junitxml=test_results.xml")

    # Run tests
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("ERRORS:", result.stderr)

        # Parse test results
        test_results = parse_test_results("test_results.xml")

        # Parse coverage if requested
        if coverage:
            try:
                with open("coverage.json", "r") as f:
                    coverage_data = json.load(f)
                test_results["coverage"] = coverage_data
            except FileNotFoundError:
                print("WARNING: Coverage report not found")
                test_results["coverage"] = {}

        return result.returncode, test_results

    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return 1, {"error": str(e)}


def parse_test_results(xml_path: str) -> Dict[str, Any]:
    """Parse test results from JUnit XML file.

    Args:
        xml_path: Path to JUnit XML file

    Returns:
        Dictionary with test results
    """
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extract test counts
        testsuite = root.find(".//testsuite")
        if testsuite is None:
            return {"error": "No test results found"}

        # Get counts
        tests = int(testsuite.get("tests", 0))
        failures = int(testsuite.get("failures", 0))
        errors = int(testsuite.get("errors", 0))
        skipped = int(testsuite.get("skipped", 0))

        # Get individual test cases
        test_cases = []
        for testcase in root.findall(".//testcase"):
            test_name = testcase.get("name", "")
            class_name = testcase.get("classname", "")
            time = float(testcase.get("time", 0))

            # Check for failures
            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped_tag = testcase.find("skipped")

            status = "passed"
            message = ""

            if failure is not None:
                status = "failed"
                message = failure.get("message", "")
            elif error is not None:
                status = "error"
                message = error.get("message", "")
            elif skipped_tag is not None:
                status = "skipped"
                message = skipped_tag.get("message", "")

            test_cases.append({
                "name": test_name,
                "class_name": class_name,
                "time": time,
                "status": status,
                "message": message
            })

        # Return results
        return {
            "tests": tests,
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "passing": tests - failures - errors - skipped,
            "test_cases": test_cases
        }

    except Exception as e:
        print(f"ERROR: Failed to parse test results: {e}")
        return {"error": str(e)}


def generate_html_report(report_data: Dict[str, Any], output_path: str):
    """Generate HTML report from test results.

    Args:
        report_data: Test report data
        output_path: Path to output HTML file
    """
    # Simple HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Campaign API Test Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            .summary {
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .summary h2 {
                margin-top: 0;
            }
            .stats {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
            }
            .stat-box {
                padding: 15px;
                border-radius: 5px;
                min-width: 120px;
                text-align: center;
            }
            .stat-box.pass {
                background-color: #dff0d8;
                color: #3c763d;
            }
            .stat-box.fail {
                background-color: #f2dede;
                color: #a94442;
            }
            .stat-box.skip {
                background-color: #fcf8e3;
                color: #8a6d3b;
            }
            .stat-box.error {
                background-color: #f2dede;
                color: #a94442;
            }
            .stat-box h3 {
                margin: 0;
                font-size: 14px;
            }
            .stat-box p {
                margin: 5px 0 0;
                font-size: 24px;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f5f5f5;
            }
            tr.failed {
                background-color: #fee;
            }
            tr.error {
                background-color: #fdd;
            }
            tr.skipped {
                background-color: #ffd;
            }
            tr.passed {
                background-color: #dfd;
            }
            .coverage {
                margin-top: 30px;
            }
            .coverage-bar {
                height: 20px;
                background-color: #e74c3c;
                position: relative;
                border-radius: 3px;
                overflow: hidden;
                margin-top: 5px;
            }
            .coverage-fill {
                height: 100%;
                background-color: #2ecc71;
                position: absolute;
                top: 0;
                left: 0;
            }
            .coverage-text {
                position: absolute;
                width: 100%;
                text-align: center;
                color: white;
                font-weight: bold;
                text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
                line-height: 20px;
            }
            .next-steps {
                margin-top: 30px;
                padding: 20px;
                background-color: #eaf3f8;
                border-radius: 5px;
            }
            .next-steps h2 {
                margin-top: 0;
                color: #2980b9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Campaign API Test Report</h1>

            <div class="summary">
                <h2>Test Summary</h2>
                <p>Generated on: {{timestamp}}</p>
                <p>Tested implementations: {{implementations}}</p>

                <div class="stats">
                    <div class="stat-box pass">
                        <h3>Passing</h3>
                        <p>{{passing}}</p>
                    </div>
                    <div class="stat-box fail">
                        <h3>Failing</h3>
                        <p>{{failures}}</p>
                    </div>
                    <div class="stat-box error">
                        <h3>Errors</h3>
                        <p>{{errors}}</p>
                    </div>
                    <div class="stat-box skip">
                        <h3>Skipped</h3>
                        <p>{{skipped}}</p>
                    </div>
                    <div class="stat-box">
                        <h3>Total</h3>
                        <p>{{tests}}</p>
                    </div>
                </div>
            </div>

            {{coverage_section}}

            <h2>Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Status</th>
                        <th>Duration (s)</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    {{test_rows}}
                </tbody>
            </table>

            <div class="next-steps">
                <h2>Next Steps</h2>
                <ul>
                    {{next_steps}}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    # Format timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format implementations
    implementations = ", ".join(report_data["implementations"])

    # Format test counts
    tests = sum(impl_data.get("tests", 0) for impl, impl_data in report_data["results"].items())
    passing = sum(impl_data.get("passing", 0) for impl, impl_data in report_data["results"].items())
    failures = sum(impl_data.get("failures", 0) for impl, impl_data in report_data["results"].items())
    errors = sum(impl_data.get("errors", 0) for impl, impl_data in report_data["results"].items())
    skipped = sum(impl_data.get("skipped", 0) for impl, impl_data in report_data["results"].items())

    # Format test rows
    test_rows = ""
    for impl, impl_data in report_data["results"].items():
        if "test_cases" in impl_data:
            for test_case in impl_data["test_cases"]:
                test_rows += f"""
                <tr class="{test_case['status']}">
                    <td>{test_case['class_name']}.{test_case['name']} <small>({impl})</small></td>
                    <td>{test_case['status'].upper()}</td>
                    <td>{test_case['time']:.3f}</td>
                    <td>{test_case['message']}</td>
                </tr>
                """

    # Format coverage section
    coverage_section = ""
    for impl, impl_data in report_data["results"].items():
        if "coverage" in impl_data:
            try:
                total_coverage = impl_data["coverage"]["totals"]["percent_covered"]
                coverage_section += f"""
                <div class="coverage">
                    <h2>Coverage for {impl} implementation</h2>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {total_coverage}%;"></div>
                        <div class="coverage-text">{total_coverage:.1f}%</div>
                    </div>
                </div>
                """
            except (KeyError, TypeError):
                coverage_section += f"""
                <div class="coverage">
                    <h2>Coverage for {impl} implementation</h2>
                    <p>Coverage data not available</p>
                </div>
                """

    # Format next steps
    next_steps = ""
    if failures > 0 or errors > 0:
        next_steps += "<li>Fix failing tests</li>"

    if "fixed" in report_data["implementations"] and "router" in report_data["implementations"]:
        next_steps += "<li>Address API inconsistencies between implementations</li>"

    next_steps += """
    <li>Implement missing endpoints according to IMPLEMENTATION_PLAN.md</li>
    <li>Standardize authentication methods</li>
    <li>Standardize response formats</li>
    <li>Add tests for any remaining edge cases</li>
    """

    # Replace template variables
    html_report = html_template
    html_report = html_report.replace("{{timestamp}}", timestamp)
    html_report = html_report.replace("{{implementations}}", implementations)
    html_report = html_report.replace("{{tests}}", str(tests))
    html_report = html_report.replace("{{passing}}", str(passing))
    html_report = html_report.replace("{{failures}}", str(failures))
    html_report = html_report.replace("{{errors}}", str(errors))
    html_report = html_report.replace("{{skipped}}", str(skipped))
    html_report = html_report.replace("{{test_rows}}", test_rows)
    html_report = html_report.replace("{{coverage_section}}", coverage_section)
    html_report = html_report.replace("{{next_steps}}", next_steps)

    # Write HTML report
    with open(output_path, "w") as f:
        f.write(html_report)

    print(f"HTML report generated: {output_path}")


def analyze_results(results: Dict[str, Dict[str, Any]]) -> List[str]:
    """Analyze test results and provide recommendations.

    Args:
        results: Test results by implementation

    Returns:
        List of recommendations
    """
    recommendations = []

    # Check if any tests are failing
    total_failures = sum(impl_data.get("failures", 0) for impl, impl_data in results.items())
    total_errors = sum(impl_data.get("errors", 0) for impl, impl_data in results.items())

    if total_failures > 0 or total_errors > 0:
        recommendations.append(f"Fix the {total_failures} failing tests and {total_errors} errors")

    # Check if fixed implementation is missing endpoints
    if "fixed" in results:
        fixed_failures = results["fixed"].get("failures", 0)
        if fixed_failures > 0:
            recommendations.append("Implement missing endpoints in fixed implementation")

    # Check if router implementation is missing endpoints
    if "router" in results:
        router_failures = results["router"].get("failures", 0)
        if router_failures > 0:
            recommendations.append("Implement missing endpoints in router implementation")

    # Check for authentication issues
    auth_failures = []
    for impl, impl_data in results.items():
        for test_case in impl_data.get("test_cases", []):
            if "auth" in test_case["name"].lower() and test_case["status"] != "passed":
                auth_failures.append(test_case["name"])

    if auth_failures:
        recommendations.append("Standardize authentication methods")

    # Check for response format issues
    format_failures = []
    for impl, impl_data in results.items():
        for test_case in impl_data.get("test_cases", []):
            if ("format" in test_case["name"].lower() or
                "response" in test_case["name"].lower()) and test_case["status"] != "passed":
                format_failures.append(test_case["name"])

    if format_failures:
        recommendations.append("Standardize response formats")

    # Check coverage
    for impl, impl_data in results.items():
        if "coverage" in impl_data:
            try:
                total_coverage = impl_data["coverage"]["totals"]["percent_covered"]
                if total_coverage < 80:
                    recommendations.append(f"Improve test coverage for {impl} implementation (currently {total_coverage:.1f}%)")
            except (KeyError, TypeError):
                pass

    # General recommendations
    recommendations.append("Refer to IMPLEMENTATION_PLAN.md for detailed steps")
    recommendations.append("Add tests for edge cases not currently covered")

    return recommendations


def main():
    """Main function."""
    args = parse_args()

    # Initialize results
    results = {}
    implementations = []

    # Run tests for fixed implementation
    if args.implementation in ["fixed", "both"]:
        implementations.append("fixed")
        fixed_exit_code, fixed_results = run_tests("fixed", args.verbose, args.coverage)
        results["fixed"] = fixed_results

    # Run tests for router implementation
    if args.implementation in ["router", "both"]:
        implementations.append("router")
        router_exit_code, router_results = run_tests("router", args.verbose, args.coverage)
        results["router"] = router_results

    # Analyze results
    recommendations = analyze_results(results)

    # Prepare report
    report = {
        "timestamp": datetime.now().isoformat(),
        "implementations": implementations,
        "results": results,
        "recommendations": recommendations
    }

    # Determine output file
    output_file = args.output or f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Write report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nTest report written to: {output_file}")

    # Generate HTML report if requested
    if args.html:
        html_output = os.path.splitext(output_file)[0] + ".html"
        generate_html_report(report, html_output)

    # Print summary
    print("\n=== Test Summary ===")
    for impl in implementations:
        print(f"\n{impl.upper()} Implementation:")
        if "error" in results[impl]:
            print(f"  ERROR: {results[impl]['error']}")
            continue

        print(f"  Tests: {results[impl].get('tests', 0)}")
        print(f"  Passing: {results[impl].get('passing', 0)}")
        print(f"  Failures: {results[impl].get('failures', 0)}")
        print(f"  Errors: {results[impl].get('errors', 0)}")
        print(f"  Skipped: {results[impl].get('skipped', 0)}")

        if "coverage" in results[impl]:
            try:
                total_coverage = results[impl]["coverage"]["totals"]["percent_covered"]
                print(f"  Coverage: {total_coverage:.1f}%")
            except (KeyError, TypeError):
                print("  Coverage: Not available")

    # Print recommendations
    print("\n=== Recommendations ===")
    for i, recommendation in enumerate(recommendations, 1):
        print(f"{i}. {recommendation}")

    # Return exit code
    if args.implementation == "both":
        exit_code = 1 if fixed_exit_code != 0 or router_exit_code != 0 else 0
    elif args.implementation == "fixed":
        exit_code = fixed_exit_code
    else:
        exit_code = router_exit_code

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
