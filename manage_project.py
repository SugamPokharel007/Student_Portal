#!/usr/bin/env python
"""Management script for running tests, checks, and maintenance tasks."""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and print status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main management function."""
    print("🎓 Sikshya Kendra Management Script")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  test       - Run all tests")
        print("  lint       - Run code quality checks")
        print("  migrate    - Run database migrations")
        print("  setup      - Initial project setup")
        print("  deploy     - Deploy to production")
        print("  dev        - Start development server")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        run_command("python -m pytest", "Running tests")
        run_command("coverage report", "Generating coverage report")
        
    elif command == "lint":
        run_command("black .", "Formatting code with Black")
        run_command("isort .", "Sorting imports")
        run_command("flake8", "Running linting checks")
        
    elif command == "migrate":
        run_command("python manage.py makemigrations", "Creating migrations")
        run_command("python manage.py migrate", "Applying migrations")
        
    elif command == "setup":
        run_command("pip install -r requirements.txt", "Installing dependencies")
        run_command("python manage.py migrate", "Setting up database")
        run_command("python manage.py collectstatic --noinput", "Collecting static files")
        print("✅ Setup completed! Create a superuser with: python manage.py createsuperuser")
        
    elif command == "deploy":
        if os.path.exists("deploy.sh"):
            run_command("chmod +x deploy.sh && ./deploy.sh", "Running deployment script")
        else:
            print("❌ deploy.sh not found")
            
    elif command == "dev":
        print("🚀 Starting development server...")
        os.system("python manage.py runserver")
        
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()