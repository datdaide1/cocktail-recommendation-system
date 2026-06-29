import os
import sys
import subprocess

def get_current_git_branch():
    """Get the current active git branch using subprocess."""
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Run git command from the directory of the script
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=script_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: Failed to retrieve current git branch. Details: {e}", file=sys.stderr)
        return None

def verify_environment():
    """Verify that both the git branch and python conda environment match expected values."""
    print("=== Starting Environment and Branch Verification ===")
    
    # 1. Verify Git Branch
    expected_branch = 'feat/phase2-backend'
    current_branch = get_current_git_branch()
    print(f"Checking Git branch: {current_branch}")
    if current_branch != expected_branch:
        print(f"Verification Failed: Expected Git branch '{expected_branch}', but got '{current_branch}'", file=sys.stderr)
        sys.exit(1)
    
    # 2. Verify Conda Environment
    expected_env = 'cocktail-ai'
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    print(f"Checking Conda environment: {conda_env}")
    if conda_env != expected_env:
        print(f"Verification Failed: Expected active Conda environment '{expected_env}', but got '{conda_env}'", file=sys.stderr)
        sys.exit(1)
        
    print("\nEnvironment and branch verified successfully!")
    sys.exit(0)

if __name__ == '__main__':
    verify_environment()
