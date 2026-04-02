from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging
import subprocess
import tempfile
import shutil
import re
from markdown import markdown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")

logger.info(f"Current working directory: {os.getcwd()}")
dict(os.environ)
#logger.info(f"Environment variables: {dict(os.environ)}")

if not api_key:
    error_msg = "GEMINI_API_KEY not found in environment variables"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Configure Gemini API
try:
    genai.configure(api_key=api_key)
    # Use Gemini 2.0 Flash model
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Gemini API configured successfully")
except Exception as e:
    error_msg = f"Failed to configure Gemini API: {str(e)}"
    logger.error(error_msg)
    raise ValueError(error_msg)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    language: str

@app.post("/debug")
async def debug_code(request: CodeRequest):
    try:
        logger.info(f"Received debug request for {request.language} code")
        logger.info(f"Code content: {request.code[:100]}...")  # Log first 100 chars of code
        
        prompt = f"Debug this {request.language} code:\n{request.code}\n\nPlease provide:\n1. Any errors found\n2. Suggested fixes\n3. Best practices recommendations"
        
        try:
            response = model.generate_content(prompt)
            if not response or not hasattr(response, 'text'):
                raise ValueError("Invalid response from Gemini API")
            
            debug_response = markdown(response.text)
            logger.info("Successfully generated debug response")
            # print(debug_response)
            
            return {
                "debug_response": debug_response,
                "status": "success"
            }
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}")
            return {
                "debug_response": f"Error from Gemini API: {str(api_error)}",
                "status": "error"
            }
            
    except Exception as e:
        error_msg = f"Error in debug_code endpoint: {str(e)}"
        logger.error(error_msg)
        return {
            "debug_response": error_msg,
            "status": "error"
        }

@app.post("/execute")
async def execute_code(request: CodeRequest):
    try:
        logger.info(f"Received execution request for {request.language} code")
        
        # Determine the execution command based on language
        ext = ""
        compile_cmd = None
        run_cmd = ""
        
        if request.language.lower() == "python":
            ext = ".py"
            run_cmd = f"python3 code{ext}"
        elif request.language.lower() in ["cpp", "c++"]:
            ext = ".cpp"
            compile_cmd = f"g++ code{ext} -o a.out"
            run_cmd = "./a.out"
        elif request.language.lower() == "c":
            ext = ".c"
            compile_cmd = f"gcc code{ext} -o a.out"
            run_cmd = "./a.out"
        elif request.language.lower() == "java":
            # For Java, the filename MUST match the class name.
            class_match = re.search(r"class\s+(\w+)", request.code)
            class_name = class_match.group(1) if class_match else "Main"
            file_name = f"{class_name}.java"
            compile_cmd = f"javac {file_name}"
            run_cmd = f"java {class_name}"
        elif request.language.lower() == "javascript":
            ext = ".js"
            run_cmd = f"node code{ext}"
        else:
            return {"output": "Unsupported language", "status": "error"}

        # Create a temporary directory to host the code file
        with tempfile.TemporaryDirectory() as tmpdir:
            # For Java, file_name is already defined
            if request.language.lower() != "java":
                file_name = f"code{ext}"
            
            file_path = os.path.join(tmpdir, file_name)
            with open(file_path, "w") as f:
                f.write(request.code)
            
            # Step 3 & 4: Use the pre-built 'debugverse-sandbox' image
            # -v mounts the temp directory to the container
            # --rm removes the container after execution
            # --network none disables network access for security
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "-v", f"{tmpdir}:/home/sandboxuser",
                "debugverse-sandbox",
                "bash", "-c",
                f"cd /home/sandboxuser && {compile_cmd + ' && ' if compile_cmd else ''} {run_cmd}"
            ]
            
            logger.info(f"Running Docker command: {' '.join(docker_cmd)}")
            
            process = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=10 # Step 3: Limited execution time
            )
            
            output = process.stdout
            errors = process.stderr
            
            status = "success" if process.returncode == 0 else "error"
            
            return {
                "output": output if status == "success" else f"STDOUT:\n{output}\n\nSTDERR:\n{errors}",
                "status": status
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Execution timed out")
        return {"output": "Error: Execution timed out (Time Limit Exceeded)", "status": "error"}
    except Exception as e:
        error_msg = f"Error in execute_code endpoint: {str(e)}"
        logger.error(error_msg)
        return {
            "output": error_msg,
            "status": "error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
