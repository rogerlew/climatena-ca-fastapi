import os, sys, pathlib, win32serviceutil, win32service, win32event, win32process
import logging, uvicorn, asyncio, threading

# ── use selector loop to avoid WinError 64 ────────────────────────
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_DIR = r"C:\ClimateNA_v7.50"                 # adjust if you moved it
LOG_PATH = pathlib.Path(BASE_DIR) / "svc.log"    # always writable by LocalSystem
os.environ["SESSIONNAME"] = "Console"
os.environ["USERPROFILE"] = r"C:\Users\Default"
os.environ["APPDATA"] = r"C:\Users\Default\AppData\Roaming"

if sys.stdout is None:
    sys.stdout = open(LOG_PATH, "a", buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout

# Custom filter to suppress /health logs
class HealthLogFilter(logging.Filter):
    def filter(self, record):
        # Check if the log message is an access log and contains "GET /health"
        if record.name == "uvicorn.access" and "GET /health" in record.getMessage():
            return False  # Suppress the log
        return True  # Allow other logs

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove existing handlers
logger.handlers.clear()

# Create a stream handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s"
))
handler.addFilter(HealthLogFilter())  # Add the filter
logger.addHandler(handler)

# Configure Uvicorn loggers
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers.clear()
uvicorn_logger.addHandler(handler)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers.clear()
uvicorn_access_logger.addHandler(handler)

logger.info("=== service bootstrap ===")
print("=== service bootstrap ===", flush=True)

import threading, asyncio, win32event, win32serviceutil, win32service, win32process
import os, uvicorn, time
from pathlib import Path
import dotenv, os

BASE_DIR =Path(r"C:\ClimateNA_v7.50\api")
dotenv.load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET missing – check your .env or service vars")

class ClimateAPI(win32serviceutil.ServiceFramework):
    _svc_name_ = "ClimateAPI"
    _svc_display_name_ = "FastAPI wrapper for Climate‑NA"
    _svc_description_ = "Serves Climate‑NA over HTTP"

    def __init__(self, *args):
        super().__init__(*args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.thread    = None        # will hold the Uvicorn thread
        self.server    = None

    def SvcDoRun(self):
        os.chdir(BASE_DIR) 
        win32process.SetPriorityClass(
            win32process.GetCurrentProcess(),
            win32process.HIGH_PRIORITY_CLASS,
        )

        cfg = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info",
            log_config=None, 
        )
        self.server = uvicorn.Server(cfg)
        self.server.install_signal_handlers = False

        def _run():
            asyncio.run(self.server.serve())

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        self.server.should_exit = True
        t.join()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(ClimateAPI)

# live debugging
# (climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py debug

# install service
# from an elevated prompt in the same conda env
# python climate_ca_api_service.py stop
# python climate_ca_api_service.py remove
# python climate_ca_api_service.py --startup auto install
# python climate_ca_api_service.py start
#
# for logging
# type C:\ClimateNA_v7.50\svc.log