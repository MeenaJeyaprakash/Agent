import os
import shutil
import subprocess
from dotenv import load_dotenv
from autogen import ConversableAgent, config_list_from_json
from urllib.parse import urlparse

try:
    import git
except ImportError:
    print("Missing dependency: gitpython. Install it using 'pip install gitpython'.")
    exit(1)

# Load environment variables at the start of your script
load_dotenv()

# Load LLM configuration
def get_llm_config():
    """Get LLM configuration from environment variables"""
    api_key = os.getenv('AZURE_API_KEY')
    if not api_key:
        raise ValueError("AZURE_API_KEY not found in .env file")
    
    llm_config = {
        "model": "gpt-4o",
        "api_type": "azure",
        "api_key": os.getenv('AZURE_API_KEY'),
        "base_url": os.getenv('AZURE_API_BASE'),
        "api_version": os.getenv('AZURE_API_VERSION'),
        "temperature": 0
    }
    
    return llm_config

# Initialize LLM configuration
llm_config = get_llm_config()

# Define Repo Cloner Agent
def clone_repo(repo_url, branch=None):
    """
    Clone a specific branch of a Git repository
    Args:
        repo_url (str): URL of the git repository
        branch (str): Name of the branch to clone
    """
    # Extract repo name from URL
    repo_name = os.path.splitext(os.path.basename(urlparse(repo_url).path))[0]
    target_path = os.path.join(".", repo_name)
    
    if os.path.exists(target_path):
        print(f"Repository {repo_name} already exists. Deleting and recloning...")
        try:
            shutil.rmtree(target_path)
        except PermissionError:
            try:
                # Make all files writable
                for root, dirs, files in os.walk(target_path):
                    for dir in dirs:
                        os.chmod(os.path.join(root, dir), 0o777)
                    for file in files:
                        os.chmod(os.path.join(root, file), 0o777)
                shutil.rmtree(target_path)
            except:
                try:
                    subprocess.run(["attrib", "-R", target_path + "\\*.*", "/S", "/D"], shell=True)
                    subprocess.run(["rmdir", "/s", "/q", target_path], shell=True)
                except:
                    print(f"Error: Could not delete directory {target_path}. Please delete it manually.")
                    return None
    
    print(f"Cloning repository {repo_name} from {repo_url}" + (f" (branch: {branch})" if branch else ""))
    try:
        if branch:
            repo = git.Repo.clone_from(repo_url, target_path, branch=branch)
        else:
            repo = git.Repo.clone_from(repo_url, target_path)
        print(f"Repository {repo_name} cloned successfully!")
        return target_path
    except git.GitCommandError as e:
        print(f"Failed to clone repository: {e}")
        return None

repo_cloner = ConversableAgent(
    name="RepoCloner",
    system_message="I clone repositories from provided Git URLs.",
    function_map={"clone_repo": clone_repo},
    llm_config=llm_config
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
    function_map={"detect_language": detect_language},
    llm_config=llm_config
)

# Define Code Builder Agent
def find_build_files(repo_path):
    """
    Find build configuration files in the repository.
    Returns a list of tuples (language, build_file_path)
    """
    build_files = {
        "java": ["pom.xml", "build.gradle"],
        "react": ["package.json"],
        "nodejs": ["package.json"],
        "python": ["requirements.txt", "setup.py", "pyproject.toml"],
        "ruby": ["Gemfile"],
        "cpp": ["CMakeLists.txt", "Makefile"]
    }
    
    found_builds = []
    for root, _, files in os.walk(repo_path):
        for lang, build_file_list in build_files.items():
            for build_file in build_file_list:
                if build_file in files:
                    found_builds.append((lang, os.path.join(root, build_file)))
    return found_builds

def build_code(repo_path, language, build_file_path=None):
    """
    Build code based on detected language and build file
    """
    build_commands = {
        "java": {
            "pom.xml": "mvn clean package",
            "build.gradle": "gradle build"
        },
        "react": {
            "package.json": "npm install && npm run build"
        },
        "nodejs": {
            "package.json": "npm install && npm start"
        },
        "python": {
            "requirements.txt": "pip install -r requirements.txt",
            "setup.py": "python setup.py install",
            "pyproject.toml": "pip install ."
        },
        "ruby": {
            "Gemfile": "bundle install"
        },
        "cpp": {
            "CMakeLists.txt": "cmake . && cmake --build .",
            "Makefile": "make"
        }
    }
    
    if language not in build_commands:
        print(f"No build instructions for {language}.")
        return "Build failed"
    
    print(f"Building {language} project...")
    try:
        original_dir = os.getcwd()
        build_dir = os.path.dirname(build_file_path) if build_file_path else repo_path
        os.chdir(build_dir)
        
        build_file = os.path.basename(build_file_path) if build_file_path else None
        if build_file in build_commands[language]:
            command = build_commands[language][build_file]
            print(f"Using build file: {build_file}")
            print(f"Executing: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            print("Build successful!")
            return result.stdout
        else:
            print(f"No specific build command for {build_file}")
            return "Build failed"
    except subprocess.CalledProcessError as e:
        print("Build failed:", e.stderr)
        return "Build failed"
    finally:
        os.chdir(original_dir)

code_builder = ConversableAgent(
    name="CodeBuilder",
    system_message="I build code based on the detected programming language.",
    function_map={"build_code": build_code},
    llm_config=llm_config
)

# Execution Workflow
def main():
    repo_url = input("Enter the GitHub repository URL (e.g., https://github.com/username/repo.git): ")
    branch = input("Enter the branch name (press Enter for default branch): ").strip() or None
    
    cloned_path = repo_cloner.function_map["clone_repo"](repo_url, branch)
    
    if cloned_path:
        # Find build files first
        build_files = find_build_files(cloned_path)
        if build_files:
            print("Found build files:")
            for lang, build_file in build_files:
                print(f"- {lang}: {build_file}")
                code_builder.function_map["build_code"](cloned_path, lang, build_file)
        else:
            # Fallback to language detection
            detected_lang = repo_analyzer.function_map["detect_language"](cloned_path)
            if detected_lang != "unknown":
                code_builder.function_map["build_code"](cloned_path, detected_lang)
            else:
                print("Could not determine the programming language or find build files.")
    else:
        print("Failed to clone repository.")

if __name__ == "__main__":
    main()
