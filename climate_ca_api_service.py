import win32serviceutil, win32service, win32event, subprocess, os

class ClimateNAService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Climate_ca_API"
    _svc_display_name_ = "ClimateNA FastAPI Service"

    def __init__(self, args):
        super().__init__(args)
        self.stop_evt = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.proc.terminate()
        win32event.SetEvent(self.stop_evt)
        
    def SvcDoRun(self):
        # change into your code folder
        os.chdir(r"C:\ClimateNA_v7.50\api")

        # path to the env’s python.exe
        python_exe = r"C:\ProgramData\anaconda3\envs\climateBC-NA\python.exe"

        # spawn Uvicorn via that interpreter
        self.proc = subprocess.Popen([
            python_exe,
            "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "1",
        ], cwd=r"C:\ClimateNA_v7.50\api")
        win32event.WaitForSingleObject(self.stop_evt, win32event.INFINITE)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(ClimateNAService)