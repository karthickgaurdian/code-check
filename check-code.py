#!/usr/bin/env python3
"""
Simple code quality checker for React/TypeScript projects
Run: python check-code.py
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

def check_project(src_dir="src"):
    """Main function to check code quality"""
    
    root = Path(src_dir)
    if not root.exists():
        print(f"❌ Error: '{src_dir}' folder not found!")
        return
    
    # Find all files
    files = list(root.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    issues = {
        "bad_naming": [],
        "any_type": [],
        "console_logs": [],
        "todos": [],
        "large_files": [],
        "deep_nesting": []
    }
    
    for file_path in files:
        rel_path = str(file_path.relative_to(Path.cwd())).replace("\\", "/")
        
        # Check file size
        lines = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.count('\n') + 1
                
                # Check for any type
                if re.search(r'\bany\b', content):
                    issues["any_type"].append(rel_path)
                
                # Check for console logs
                if re.search(r'console\.(log|warn|error|debug)', content):
                    issues["console_logs"].append(rel_path)
                
                # Check for TODOs
                if re.search(r'\b(TODO|FIXME|HACK|BUG)\b', content):
                    issues["todos"].append(rel_path)
        except:
            pass  # Skip binary files
        
        # Check file size (>300 lines)
        if lines > 300:
            issues["large_files"].append(f"{rel_path} ({lines} lines)")
        
        # Check naming conventions for TypeScript/React files
        if file_path.suffix in ['.tsx', '.ts', '.jsx']:
            name = file_path.stem
            
            # Component files should be PascalCase
            if file_path.suffix == '.tsx' and 'hooks' not in str(file_path.parent):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                    issues["bad_naming"].append(f"{rel_path} (components should be PascalCase)")
            
            # Hook files should start with 'use'
            if 'hooks' in str(file_path.parent) and not name.startswith('use'):
                issues["bad_naming"].append(f"{rel_path} (hooks should start with 'use')")
            
            # Utility files should be camelCase
            if 'utils' in str(file_path.parent) and name != 'index':
                if not re.match(r'^[a-z][a-zA-Z0-9]*$', name):
                    issues["bad_naming"].append(f"{rel_path} (utils should be camelCase)")
        
        # Check folder depth (more than 4 levels deep)
        depth = len(file_path.relative_to(root).parents)
        if depth > 4:
            issues["deep_nesting"].append(f"{rel_path} (depth: {depth})")
    
    # Print report
    print("\n" + "="*60)
    print("📊 CODE QUALITY REPORT")
    print("="*60)
    
    total_issues = 0
    for category, items in issues.items():
        if items:
            print(f"\n❌ {category.replace('_', ' ').upper()}: {len(items)}")
            for item in items[:10]:  # Show first 10
                print(f"   • {item}")
            if len(items) > 10:
                print(f"   ... and {len(items)-10} more")
            total_issues += len(items)
    
    if total_issues == 0:
        print("\n✅ Great! No issues found!")
    else:
        print(f"\n📈 Total issues found: {total_issues}")
    
    print("="*60)

if __name__ == "__main__":
    # Check if src folder exists
    if len(sys.argv) > 1:
        check_project(sys.argv[1])
    else:
        check_project("src")
