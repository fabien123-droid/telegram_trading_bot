#!/usr/bin/env python3
"""
Test runner script for the Telegram Trading Bot.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-asyncio',
        'pandas',
        'numpy',
        'sqlalchemy',
        'aiohttp',
        'websockets'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed")
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    command = "python -m pytest tests/"
    
    if verbose:
        command += " -v"
    
    if coverage:
        command += " --cov=. --cov-report=html --cov-report=term-missing"
    
    return run_command(command, "Running Unit Tests")


def run_specific_test(test_file, verbose=False):
    """Run a specific test file."""
    command = f"python -m pytest {test_file}"
    
    if verbose:
        command += " -v"
    
    return run_command(command, f"Running {test_file}")


def run_linting():
    """Run code linting."""
    commands = [
        ("python -m flake8 --max-line-length=100 --ignore=E203,W503 .", "Flake8 Linting"),
        ("python -m black --check --diff .", "Black Code Formatting Check"),
        ("python -m isort --check-only --diff .", "Import Sorting Check")
    ]
    
    all_passed = True
    
    for command, description in commands:
        try:
            if not run_command(command, description):
                all_passed = False
        except Exception:
            print(f"⚠️  {description} tool not installed, skipping...")
    
    return all_passed


def run_type_checking():
    """Run type checking with mypy."""
    try:
        return run_command("python -m mypy . --ignore-missing-imports", "Type Checking with MyPy")
    except Exception:
        print("⚠️  MyPy not installed, skipping type checking...")
        return True


def run_security_check():
    """Run security checks."""
    try:
        return run_command("python -m bandit -r . -x tests/", "Security Check with Bandit")
    except Exception:
        print("⚠️  Bandit not installed, skipping security check...")
        return True


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("📊 GENERATING COMPREHENSIVE TEST REPORT")
    print("="*60)
    
    # Run tests with coverage and generate reports
    command = """
    python -m pytest tests/ \
        --cov=. \
        --cov-report=html \
        --cov-report=xml \
        --cov-report=term-missing \
        --junitxml=test-results.xml \
        -v
    """
    
    return run_command(command, "Generating Test Report")


def run_performance_tests():
    """Run performance tests."""
    print("\n" + "="*60)
    print("⚡ RUNNING PERFORMANCE TESTS")
    print("="*60)
    
    # Create a simple performance test
    perf_test_code = '''
import time
import pandas as pd
import numpy as np
from analysis.technical_indicators import TechnicalIndicators

def test_performance():
    """Test performance with large dataset."""
    print("Creating large dataset...")
    
    # Create 10k data points
    dates = pd.date_range(start="2020-01-01", periods=10000, freq="1H")
    np.random.seed(42)
    
    prices = [100.0]
    for _ in range(9999):
        change = np.random.normal(0, 0.01)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))
    
    data = pd.DataFrame({
        "timestamp": dates,
        "open": prices[:-1] + [prices[-1]],
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "close": prices,
        "volume": np.random.randint(1000, 10000, 10000)
    })
    
    print(f"Dataset created: {len(data)} rows")
    
    # Test indicators performance
    indicators = TechnicalIndicators()
    
    start_time = time.time()
    result = indicators.get_all_indicators(data)
    end_time = time.time()
    
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Performance: {len(data)/execution_time:.0f} rows/second")
    
    if execution_time > 10:
        print("⚠️  Performance warning: Execution took longer than 10 seconds")
        return False
    else:
        print("✅ Performance test passed")
        return True

if __name__ == "__main__":
    test_performance()
'''
    
    # Write and run performance test
    with open("temp_perf_test.py", "w") as f:
        f.write(perf_test_code)
    
    try:
        result = run_command("python temp_perf_test.py", "Performance Test")
        os.remove("temp_perf_test.py")
        return result
    except Exception as e:
        print(f"Error running performance test: {e}")
        if os.path.exists("temp_perf_test.py"):
            os.remove("temp_perf_test.py")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for Telegram Trading Bot")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--type-check", action="store_true", help="Run type checking only")
    parser.add_argument("--security", action="store_true", help="Run security checks only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive report")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🤖 Telegram Trading Bot - Test Runner")
    print("="*60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    success = True
    
    # Run specific test file
    if args.file:
        success = run_specific_test(args.file, args.verbose)
    
    # Run individual test types
    elif args.unit:
        success = run_unit_tests(args.verbose, args.coverage)
    
    elif args.lint:
        success = run_linting()
    
    elif args.type_check:
        success = run_type_checking()
    
    elif args.security:
        success = run_security_check()
    
    elif args.performance:
        success = run_performance_tests()
    
    elif args.report:
        success = generate_test_report()
    
    # Run all tests
    elif args.all or len(sys.argv) == 1:
        print("🚀 Running comprehensive test suite...")
        
        tests = [
            (lambda: run_unit_tests(args.verbose, True), "Unit Tests with Coverage"),
            (run_linting, "Code Linting"),
            (run_type_checking, "Type Checking"),
            (run_security_check, "Security Checks"),
            (run_performance_tests, "Performance Tests")
        ]
        
        results = []
        
        for test_func, test_name in tests:
            print(f"\n🔄 Running {test_name}...")
            result = test_func()
            results.append((test_name, result))
            if not result:
                success = False
        
        # Print summary
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<30} {status}")
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n💥 Some tests failed!")
    
    # Generate final report
    if args.all or args.report:
        print("\n📊 Test artifacts generated:")
        
        artifacts = [
            ("htmlcov/index.html", "Coverage Report (HTML)"),
            ("coverage.xml", "Coverage Report (XML)"),
            ("test-results.xml", "Test Results (JUnit XML)")
        ]
        
        for artifact, description in artifacts:
            if os.path.exists(artifact):
                print(f"✅ {description}: {artifact}")
            else:
                print(f"❌ {description}: Not generated")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

