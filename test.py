import os
import subprocess
import autogen
import requests

# Configuration for AI model
api_key    = "0911999a1afe4ccdaa361cb2c801ee11"
llm_config = {"model": "gpt-4o",
              "api_type": "azure",
              "api_key": api_key,   
              "base_url": "https://aiinfusedterraformmodel.cognitiveservices.azure.com/",         
              "api_version": "2024-08-01-preview",
              "temperature": 0}

# Define the AutoGen AI Agent
build_agent = autogen.AssistantAgent(
    name="Build_Agent",
    description="An AI agent that automates the Java build process and handles errors",
    llm_config=llm_config
)

# Function to detect build tool
def detect_build_tool(repo_path):
    if os.path.exists(os.path.join(repo_path, "pom.xml")):
        return "maven"
    elif os.path.exists(os.path.join(repo_path, "build.gradle")):
        return "gradle"
    else:
        return None

# Function to execute the Java build process
def build_java_project(repo_path):
    build_tool = detect_build_tool(repo_path)
    
    if build_tool == "maven":
        build_command = "mvn clean package"
    elif build_tool == "gradle":
        build_command = "gradle build"
    else:
        return "No Java build tool detected in the repository."

    try:
        result = subprocess.run(
            build_command, shell=True, cwd=repo_path, capture_output=True, text=True
        )

        if result.returncode == 0:
            return "Build successful!"
        else:
            error_msg = result.stderr
            fix_suggestion = build_agent.chat(
                [
                    {"role": "system", "content": "You are an AI expert in Java and DevOps, fixing build issues."},
                    {"role": "user", "content": f"Build failed with error:\n{error_msg}. How can I fix it?"}
                ]
            )
            return f"Build failed. AI Suggestion: {fix_suggestion}"
    
    except Exception as e:
        return f"Error executing build: {str(e)}"



# Example Usage
repo_path = "c:/Users/Autogen/Desktop/Agent-setup/Agent/Java-Project"
print(build_java_project(repo_path))
