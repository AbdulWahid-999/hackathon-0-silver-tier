"""
Silver Tier Verification Script
Tests all Silver Tier requirements to ensure they are working

Run: python test_silver_tier.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Vault paths
VAULT_BASE = Path(r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault")
PROJECT_ROOT = Path(r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier")

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    status_color = Colors.GREEN if passed else Colors.RED
    print(f"{status_color}{status}{Colors.END} - {name}")
    if details:
        print(f"       {details}")

def test_bronze_requirements():
    """Test all Bronze Tier requirements (prerequisites)"""
    print_header("Bronze Tier Requirements (Prerequisites)")
    
    all_passed = True
    
    # Test 1: Vault structure
    required_folders = ['Inbox', 'Needs_Action', 'Done', 'Plans', 'Pending_Approval', 'Approved', 'Rejected', 'Logs']
    folders_exist = all((VAULT_BASE / folder).exists() for folder in required_folders)
    print_test("Vault folder structure", folders_exist, f"Required: {', '.join(required_folders)}")
    all_passed &= folders_exist
    
    # Test 2: Dashboard.md exists
    dashboard_exists = (VAULT_BASE / 'Dashboard.md').exists()
    print_test("Dashboard.md exists", dashboard_exists)
    all_passed &= dashboard_exists
    
    # Test 3: Company_Handbook.md exists
    handbook_exists = (VAULT_BASE / 'Company_Handbook.md').exists()
    print_test("Company_Handbook.md exists", handbook_exists)
    all_passed &= handbook_exists
    
    # Test 4: File Watcher exists and works
    file_watcher_exists = (PROJECT_ROOT / 'file_watcher.py').exists()
    print_test("File Watcher script exists", file_watcher_exists)
    all_passed &= file_watcher_exists
    
    # Test 5: Files processed (check Done folder)
    done_files = list((VAULT_BASE / 'Done').glob('*.md'))
    files_processed = len(done_files) > 0
    print_test("Files processed successfully", files_processed, f"Found {len(done_files)} completed files")
    all_passed &= files_processed
    
    return all_passed

def test_silver_watchers():
    """Test Silver Tier watcher scripts"""
    print_header("Silver Tier: Watcher Scripts")
    
    all_passed = True
    
    # Test 1: Gmail Watcher exists
    gmail_watcher_exists = (PROJECT_ROOT / 'gmail_watcher.py').exists()
    print_test("Gmail Watcher script exists", gmail_watcher_exists)
    all_passed &= gmail_watcher_exists
    
    # Test 2: LinkedIn Watcher exists
    linkedin_watcher_exists = (PROJECT_ROOT / 'linkedin_watcher.py').exists()
    print_test("LinkedIn Watcher script exists", linkedin_watcher_exists)
    all_passed &= linkedin_watcher_exists
    
    # Test 3: File Watcher path is correct
    file_watcher_path = PROJECT_ROOT / 'file_watcher.py'
    if file_watcher_path.exists():
        content = file_watcher_path.read_text()
        correct_path = 'Silver-Tier' in content and 'Bronze-Tier' not in content
        print_test("File Watcher path configuration", correct_path, "Should point to Silver-Tier vault")
        all_passed &= correct_path
    
    # Test 4: Gmail Watcher path is correct
    gmail_watcher_path = PROJECT_ROOT / 'gmail_watcher.py'
    if gmail_watcher_path.exists():
        content = gmail_watcher_path.read_text()
        correct_path = 'Silver-Tier' in content and 'Bronze-Tier' not in content
        print_test("Gmail Watcher path configuration", correct_path, "Should point to Silver-Tier vault")
        all_passed &= correct_path
    
    # Test 5: Requirements file
    requirements_exists = (PROJECT_ROOT / 'requirements.txt').exists()
    print_test("Python requirements.txt exists", requirements_exists)
    all_passed &= requirements_exists
    
    return all_passed

def test_mcp_server():
    """Test MCP Email Server"""
    print_header("Silver Tier: MCP Server")
    
    all_passed = True
    
    # Test 1: MCP server exists
    mcp_server_exists = (PROJECT_ROOT / 'mcp-email-server.js').exists()
    print_test("MCP Email Server exists", mcp_server_exists)
    all_passed &= mcp_server_exists
    
    # Test 2: MCP server path configuration
    if mcp_server_exists:
        content = (PROJECT_ROOT / 'mcp-email-server.js').read_text()
        correct_path = 'Silver-Tier' in content and 'Bronze-Tier' not in content
        print_test("MCP Server path configuration", correct_path, "Should point to Silver-Tier vault")
        all_passed &= correct_path
    
    # Test 3: Package.json exists
    package_json_exists = (PROJECT_ROOT / 'package.json').exists()
    print_test("package.json exists", package_json_exists)
    all_passed &= package_json_exists
    
    # Test 4: Node modules installed
    node_modules_exists = (PROJECT_ROOT / 'node_modules').exists()
    print_test("Node modules installed", node_modules_exists)
    all_passed &= node_modules_exists
    
    return all_passed

def test_approval_workflow():
    """Test Human-in-the-Loop Approval Workflow"""
    print_header("Silver Tier: HITL Approval Workflow")
    
    all_passed = True
    
    # Test 1: Approval workflow script exists
    approval_script_exists = (PROJECT_ROOT / 'approval_workflow.py').exists()
    print_test("Approval workflow script exists", approval_script_exists)
    all_passed &= approval_script_exists
    
    # Test 2: Approval folders exist
    approval_folders = ['Pending_Approval', 'Approved', 'Rejected']
    folders_exist = all((VAULT_BASE / folder).exists() for folder in approval_folders)
    print_test("Approval folders exist", folders_exist, f"Required: {', '.join(approval_folders)}")
    all_passed &= folders_exist
    
    # Test 3: .env file exists
    env_file_exists = (PROJECT_ROOT / '.env').exists()
    print_test(".env file exists", env_file_exists, "Required for credentials")
    all_passed &= env_file_exists
    
    return all_passed

def test_scheduling():
    """Test Scheduling System"""
    print_header("Silver Tier: Scheduling")
    
    all_passed = True
    
    # Test 1: Scheduler script exists
    scheduler_exists = (PROJECT_ROOT / 'scheduler.py').exists()
    print_test("Scheduler script exists", scheduler_exists)
    all_passed &= scheduler_exists
    
    # Test 2: Briefings folder exists
    briefings_folder_exists = (VAULT_BASE / 'Briefings').exists()
    print_test("Briefings folder exists", briefings_folder_exists, "For CEO Briefings")
    all_passed &= briefings_folder_exists
    
    return all_passed

def test_orchestrator():
    """Test Orchestrator"""
    print_header("Silver Tier: Orchestrator")
    
    all_passed = True
    
    # Test 1: Orchestrator script exists
    orchestrator_exists = (PROJECT_ROOT / 'orchestrator.py').exists()
    print_test("Orchestrator script exists", orchestrator_exists)
    all_passed &= orchestrator_exists
    
    return all_passed

def test_ralph_wiggum():
    """Test Ralph Wiggum Loop"""
    print_header("Silver Tier: Ralph Wiggum Loop")
    
    all_passed = True
    
    # Test 1: Ralph Wiggum script exists
    ralph_exists = (PROJECT_ROOT / 'ralph-wiggum-loop.js').exists()
    print_test("Ralph Wiggum loop script exists", ralph_exists)
    all_passed &= ralph_exists
    
    # Test 2: Ralph Wiggum config exists
    ralph_config_exists = (PROJECT_ROOT / 'config_ralph_wiggum.json').exists()
    print_test("Ralph Wiggum configuration exists", ralph_config_exists)
    all_passed &= ralph_config_exists
    
    # Test 3: Ralph Wiggum documentation exists
    ralph_readme_exists = (PROJECT_ROOT / 'README-RALPH-WIGGUM.md').exists()
    print_test("Ralph Wiggum documentation exists", ralph_readme_exists)
    all_passed &= ralph_readme_exists
    
    return all_passed

def test_agent_skills():
    """Test Agent Skills Documentation"""
    print_header("Silver Tier: Agent Skills")
    
    all_passed = True
    
    # Test 1: Agent Skills documentation exists
    agent_skills_exists = (PROJECT_ROOT / 'AGENT_SKILLS.md').exists()
    print_test("Agent Skills documentation exists", agent_skills_exists)
    all_passed &= agent_skills_exists
    
    return all_passed

def test_documentation():
    """Test Documentation"""
    print_header("Silver Tier: Documentation")
    
    all_passed = True
    
    # Test various documentation files
    docs = [
        'README.md',
        'SILVER-TIER-README.md',
        'AGENT_SKILLS.md',
        'README-MCP-EMAIL.md',
        'README-RALPH-WIGGUM.md',
        'DEPLOYMENT-GUIDE.md'
    ]
    
    for doc in docs:
        doc_exists = (PROJECT_ROOT / doc).exists()
        print_test(f"Documentation: {doc}", doc_exists)
        all_passed &= doc_exists
    
    return all_passed

def test_dependencies():
    """Test Dependencies"""
    print_header("Silver Tier: Dependencies")
    
    all_passed = True
    
    # Test Python dependencies
    try:
        import watchdog
        print_test("Python: watchdog installed", True)
    except ImportError:
        print_test("Python: watchdog installed", False, "Run: pip install -r requirements.txt")
        all_passed &= False
    
    try:
        import schedule
        print_test("Python: schedule installed", True)
    except ImportError:
        print_test("Python: schedule installed", False, "Run: pip install -r requirements.txt")
        all_passed &= False
    
    try:
        import dotenv
        print_test("Python: python-dotenv installed", True)
    except ImportError:
        print_test("Python: python-dotenv installed", False, "Run: pip install -r requirements.txt")
        all_passed &= False
    
    # Test Node.js dependencies
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_test("Node.js installed", True, result.stdout.strip())
        else:
            print_test("Node.js installed", False)
            all_passed &= False
    except Exception:
        print_test("Node.js installed", False, "Install Node.js 16+")
        all_passed &= False
    
    return all_passed

def main():
    """Run all tests"""
    print_header("🧪 SILVER TIER VERIFICATION TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Vault Path: {VAULT_BASE}")
    
    results = {}
    
    # Run all tests
    results['Bronze Requirements'] = test_bronze_requirements()
    results['Watcher Scripts'] = test_silver_watchers()
    results['MCP Server'] = test_mcp_server()
    results['Approval Workflow'] = test_approval_workflow()
    results['Scheduling'] = test_scheduling()
    results['Orchestrator'] = test_orchestrator()
    results['Ralph Wiggum Loop'] = test_ralph_wiggum()
    results['Agent Skills'] = test_agent_skills()
    results['Documentation'] = test_documentation()
    results['Dependencies'] = test_dependencies()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} categories passed{Colors.END}")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SILVER TIER COMPLETE! All requirements satisfied.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ Some requirements not met. Review failures above.{Colors.END}")
    
    # Silver Tier Requirements Checklist
    print_header("📋 SILVER TIER REQUIREMENTS CHECKLIST")
    
    requirements = [
        ("All Bronze requirements", results['Bronze Requirements']),
        ("2+ Watcher scripts (File + Gmail + LinkedIn)", results['Watcher Scripts']),
        ("Auto-post LinkedIn", results['Watcher Scripts'] and results['Documentation']),
        ("Claude reasoning loop (Plan.md)", results['Orchestrator'] and results['Ralph Wiggum Loop']),
        ("Working MCP server", results['MCP Server']),
        ("HITL approval workflow", results['Approval Workflow']),
        ("Basic scheduling", results['Scheduling']),
        ("Agent Skills documentation", results['Agent Skills']),
    ]
    
    for req, passed in requirements:
        status = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
        print(f"{status} {req}")
    
    silver_complete = all(passed for _, passed in requirements)
    
    print(f"\n{'='*60}")
    if silver_complete:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SILVER TIER: 100% COMPLETE{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ SILVER TIER: INCOMPLETE{Colors.END}")
    print(f"{'='*60}\n")
    
    return 0 if silver_complete else 1

if __name__ == "__main__":
    sys.exit(main())
