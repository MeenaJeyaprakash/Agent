import os
import shutil
import subprocess
from autogen import ConversableAgent

try:
    import git
except ImportError:
    print("Missing dependency: gitpython. Install it using 'pip install gitpython'.")
    exit(1)

# Define Repo Cloner Agent
def clone_repo(repo_url, clone_path="./cloned_repo"):
    if os.path.exists(clone_path):
        print("Repository already exists. Deleting and recloning...")
        try:
            shutil.rmtree(clone_path)
            #subprocess.run(["rmdir", "-rf", clone_path], check=True)
        except PermissionError:
            try:
                #Make all files writable
                for root, dirs, files in os.walk(clone_path):
                    for dir in dirs:
                        os.chmod(os.path.join(root, dir), 0o777)
                    for file in files:
                        os.chmod(os.path.join(root, file), 0o777)
                # Try again
                shutil.rmtree(clone_path)
            except:
                try:
                    # If still not able to delete, try with subprocess on windows
                    subprocess.run(["attrib", "-R", clone_path + "\\*.*", "/S", "/D"], shell=True)
                    subprocess.run(["rmdir", "/s", "/q", clone_path], shell=True)
                except:
                    print(f"Error: Could not delete directory {clone_path}. Please delete it manually.")
        #except FileNotFoundError:
            #print(f"Warning: Directory {clone_path} not found. Proceeding with cloning.")
    
    print(f"Cloning repository from {repo_url}...")
    git.Repo.clone_from(repo_url, clone_path)
    print("Repository cloned successfully!")
    return clone_path

repo_cloner = ConversableAgent(
    name="RepoCloner",
    system_message="I clone repositories from provided Git URLs.",
    function_map={"clone_repo": clone_repo}
)

# Define Repo Analyzer Agent
def detect_language(repo_path):
    extensions = {
        "java": ".java",
        "python": ".py",
        "ruby": ".rb",
        "cpp": ".cpp",
        "react": ".jsx",
        "nodejs": ".js",
    }
    build_files = {
        "java": "pom.xml",
        "react": "package.json",
        "nodejs": "package.json",
        "python": "requirements.txt",
        "ruby": "Gemfile",
        "cpp": "Makefile",
    }
    lang_count = {}
    detected_build_file = None
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            for lang, ext in extensions.items():
                if file.endswith(ext):
                    lang_count[lang] = lang_count.get(lang, 0) + 1
            for lang, build_file in build_files.items():
                if file.lower() == build_file.lower():
                    detected_build_file = lang
    
    detected_language = detected_build_file if detected_build_file else (max(lang_count, key=lang_count.get) if lang_count else "unknown")
    print(f"Detected language: {detected_language}")
    return detected_language

repo_analyzer = ConversableAgent(
    name="RepoAnalyzer",
    system_message="I analyze repositories and detect their primary programming language.",
    function_map={"detect_language": detect_language}
)

# Define Code Builder Agent
def build_code(repo_path, language):
    build_commands = {
        "java": "mvn clean package",
        "react": "npm install && npm run build",
        "nodejs": "npm install && npm start",
        "python": "python -m compileall .",
        "ruby": "ruby -c main.rb",
        "cpp": "g++ -o output main.cpp",
    }
    
    if language not in build_commands:
        print(f"No build instructions for {language}.")
        return "Build failed"
    
    print(f"Building {language} project...")
    try:
        original_dir = os.getcwd()
        os.chdir(repo_path)
        result = subprocess.run(build_commands[language], shell=True, capture_output=True, text=True, check=True)
        print("Build successful!")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Build failed:", e.stderr)
        return "Build failed"
    finally:
        os.chdir(original_dir)

code_builder = ConversableAgent(
    name="CodeBuilder",
    system_message="I build code based on the detected programming language.",
    function_map={"build_code": build_code}
)

# Execution Workflow
def main():
    repo_url = "https://github.com/MeenaJeyaprakash/Agent.git"
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    #repo_url = input("Enter Git repository URL: ")
    cloned_path = repo_cloner.function_map["clone_repo"](repo_url)
    detected_lang = repo_analyzer.function_map["detect_language"](cloned_path)
    if detected_lang != "unknown":
        code_builder.function_map["build_code"](cloned_path, detected_lang)
    else:
        print("Could not determine the programming language.")

if __name__ == "__main__":
    main()
