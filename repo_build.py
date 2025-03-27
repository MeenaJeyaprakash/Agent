import os
import shutil
import subprocess
from pathlib import Path
from autogen import UserProxyAgent, AssistantAgent

# Set up agents
config_list = [
    {"model": "gpt-4o",
              "api_type": "azure",
              "api_key": "0911999a1afe4ccdaa361cb2c801ee11",   
              "base_url": "https://aiinfusedterraformmodel.cognitiveservices.azure.com/",         
              "api_version": "2024-08-01-preview",
              "temperature": 0}
]

# Clone Repository
def clone_repository(repo_url, repo_dir="cloned_repo"):
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)  # Clean previous clone
    subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
    return repo_dir

# Analyze Project Structure
def detect_project_type(repo_dir):
    files = [f.name for f in Path(repo_dir).glob("**/*") if f.is_file()]

    if "pom.xml" in files:
        return "java-maven"
    elif "package.json" in files and "node_modules" not in files:
        return "react"
    elif any(f.endswith(".py") for f in files) and "requirements.txt" in files:
        return "python"
    elif any(f.endswith(".cpp") or f.endswith(".h") for f in files):
        return "cpp"
    elif "Gemfile" in files:
        return "ruby"
    else:
        return "unknown"

# Build Based on Detected Type
def build_project(repo_dir, project_type):
    commands = {
        "java-maven": ["mvn", "clean", "package"],
        "python": ["pip", "install", "-r", "requirements.txt"],
        "react": ["npm", "install", "&&", "npm", "run", "build"],
        "cpp": ["g++", "*.cpp", "-o", "output"],
        "ruby": ["bundle", "install"]
    }
    
    if project_type in commands:
        print(f"Building {project_type} project...")
        subprocess.run(commands[project_type], cwd=repo_dir, shell=True, check=True)
    else:
        print("Unsupported project type.")

# Create Agents
repo_manager = AssistantAgent(name="RepoManager", system_message="Handles repo cloning.", config_list=config_list)
analyzer = AssistantAgent(name="Analyzer", system_message="Analyzes the repo to determine project type.", config_list=config_list)
builder = AssistantAgent(name="Builder", system_message="Builds the project based on type.", config_list=config_list)

# Define Execution Flow
def execute_pipeline(repo_url):
    repo_dir = repo_manager.call(clone_repository, repo_url)
    project_type = analyzer.call(detect_project_type, repo_dir)
    builder.call(build_project, repo_dir, project_type)

# Example Usage
repo_url = "https://github.com/example/repo.git"  # Change to your repo
execute_pipeline(repo_url)
