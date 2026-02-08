#!/usr/bin/env python3
"""
SOC Risk Engine — Integration Smoke Test

Verifies that the live stack is running and responsive.
Does NOT create or modify any data — only checks health endpoints.

Usage:
    python scripts/smoke_test.py
    make smoke
"""

import sys
import requests

THEHIVE_URL = "http://localhost:9000"
CORTEX_URL = "http://localhost:9001"
ES_URL = "http://localhost:9200"

passed = 0
failed = 0


def check(name: str, url: str, expected_status: int = 200) -> bool:
    global passed, failed
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == expected_status:
            print(f"  [PASS] {name} — {url} ({resp.status_code})")
            passed += 1
            return True
        else:
            print(f"  [FAIL] {name} — {url} (got {resp.status_code}, expected {expected_status})")
            failed += 1
            return False
    except requests.ConnectionError:
        print(f"  [FAIL] {name} — {url} (connection refused)")
        failed += 1
        return False
    except requests.Timeout:
        print(f"  [FAIL] {name} — {url} (timed out)")
        failed += 1
        return False


def main():
    print("=" * 60)
    print("  SOC Risk Engine — Smoke Test")
    print("=" * 60)
    print()

    # Infrastructure
    print("Infrastructure Services:")
    check("Elasticsearch", f"{ES_URL}/_cluster/health")
    check("Cortex API",    f"{CORTEX_URL}/api/status")
    check("TheHive API",   f"{THEHIVE_URL}/api/status")
    print()

    # Summary
    total = passed + failed
    print("-" * 60)
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print("-" * 60)

    if failed > 0:
        print("\nSome checks failed. Ensure all services are running:")
        print("  docker compose ps")
        print("  docker compose logs -f")
        sys.exit(1)
    else:
        print("\nAll checks passed. Stack is healthy.")
        sys.exit(0)


if __name__ == "__main__":
    main()
