Clone the project to your Local machine
```bash
git clone https://github.com/bhola-dev58/DebugVerse.git
```
# How to run the project

## 1. Quick Setup (Recommended)

Run the setup script from the root directory to create a virtual environment, install backend dependencies, and setup the frontend:

```bash
chmod +x setup.sh
./setup.sh
```

## 2. To Run the Project

After setup, you can start both the backend and frontend concurrently using the run script:

```bash
chmod +x run.sh
./run.sh
```

Alternatively, you can run them manually:

### Run Backend 
```bash
source venv/bin/activate
cd backend
uvicorn main:app --reload
```

### Run Frontend
```bash
cd frontend
npm start
```

## Environment Variables
Make sure you have a `.env` file in the `backend` directory with your Gemini API Key:
```
GEMINI_API_KEY=your_api_key_here
```
