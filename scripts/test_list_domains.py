#!/usr/bin/env python3
"""
Standalone script to test domain listing.

Usage:
  python scripts/test_list_domains.py                    Run unit tests for list_domains
  python scripts/test_list_domains.py <path_to.gdb>     List domains in a real FGDB (requires arcpy)
"""
import sys
import os
import json


def run_unit_tests():
    """Run pytest for list_domains-related tests."""
    import pytest
    # Run only tests that cover list_domains
    args = [
        "tests/test_gdb.py::TestFileGDBBackend::test_list_domains_coded_value_and_range",
        "tests/test_gdb.py::TestFileGDBBackend::test_list_domains_empty",
        "tests/test_gdb.py::TestFileGDBBackend::test_list_domains_none_return",
        "tests/test_gdb_tools.py::TestGDBTools::test_list_domains",
        "tests/test_fgdb_toolserver.py::TestListDomains::test_list_domains_success",
        "tests/test_fgdb_toolserver.py::TestListDomains::test_list_domains_error",
        "-v",
    ]
    return pytest.main(args)


def list_domains_live(gdb_path: str) -> None:
    """Connect to a real FGDB and list domains (requires arcpy)."""
    try:
        import arcpy  # noqa: F401
    except ImportError:
        print("arcpy is not available. Use this script with a path only in an ArcGIS Python environment.")
        sys.exit(1)

    gdb_path = os.path.abspath(gdb_path)
    if not os.path.isdir(gdb_path) or not gdb_path.lower().endswith(".gdb"):
        print(f"Invalid geodatabase path: {gdb_path}")
        sys.exit(1)

    from dtos.requestobjects import Connection
    from gdb_ops.gdb_tools import create_tools_from_env

    print(f"Connecting to: {gdb_path}\n")
    try:
        conn = Connection(connection_string=gdb_path)
        tools = create_tools_from_env(conn)
        domains = tools.list_domains()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Found {len(domains)} domain(s)\n")
    print(json.dumps(domains, indent=2, default=str))


def main():
    if len(sys.argv) > 1:
        gdb_path = sys.argv[1]
        list_domains_live(gdb_path)
    else:
        print("Running unit tests for list_domains...\n")
        exit_code = run_unit_tests()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
