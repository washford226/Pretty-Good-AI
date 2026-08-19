import os
import subprocess
import sys
import time


def main() -> None:
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print("Set NGROK_AUTHTOKEN first, then run this script.")
        print("Example: $env:NGROK_AUTHTOKEN='your_token'; python start_tunnel.py")
        return

    subprocess.Popen(["ngrok", "http", "8000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    print("ngrok tunnel started on port 8000")
    print("Use APP_BASE_URL=https://<your-ngrok-subdomain>.ngrok-free.app")


if __name__ == "__main__":
    main()
