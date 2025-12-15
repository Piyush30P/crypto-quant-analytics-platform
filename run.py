"""
Main application launcher - starts backend and frontend
"""
import subprocess
import sys
import time
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from backend.storage.database import init_db
from loguru import logger


def setup_logging():
    """Configure logging"""
    logger.add(
        settings.LOG_FILE,
        rotation="500 MB",
        retention="10 days",
        level=settings.LOG_LEVEL
    )


def initialize_database():
    """Initialize database and create tables"""
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


def start_backend():
    """Start FastAPI backend server"""
    logger.info(f"Starting FastAPI backend on {settings.API_HOST}:{settings.API_PORT}")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.api.main:app",
        "--host", settings.API_HOST,
        "--port", str(settings.API_PORT),
        "--reload" if settings.API_RELOAD else "--no-reload"
    ]
    return subprocess.Popen(backend_cmd)


def start_frontend():
    """Start Streamlit frontend"""
    logger.info(f"Starting Streamlit frontend on port {settings.FRONTEND_PORT}")
    frontend_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port", str(settings.FRONTEND_PORT),
        "--server.headless", "true"
    ]
    return subprocess.Popen(frontend_cmd)


def main():
    """Main application entry point"""
    print("=" * 60)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    print()
    
    # Setup
    setup_logging()
    logger.info("Starting application...")
    
    # Initialize database
    initialize_database()
    
    # Start services
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        processes.append(backend_process)
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print()
        print("✅ Application started successfully!")
        print()
        print(f"📊 Dashboard: http://localhost:{settings.FRONTEND_PORT}")
        print(f"🔌 API: http://localhost:{settings.API_PORT}")
        print(f"📚 API Docs: http://localhost:{settings.API_PORT}/docs")
        print()
        print("Press Ctrl+C to stop...")
        print()
        
        # Keep running
        while True:
            time.sleep(1)
            # Check if any process has died
            for p in processes:
                if p.poll() is not None:
                    logger.error("A service has stopped unexpectedly")
                    raise KeyboardInterrupt
                    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        print("\n🛑 Shutting down services...")
        
        # Terminate all processes
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        
        print("✅ Shutdown complete")
        logger.info("Application stopped")


if __name__ == "__main__":
    main()
