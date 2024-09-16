import sys
import websocket
import uuid
import time
import subprocess
import json
import requests
import threading
import os
import signal
import atexit
from threading import Lock

rtl_process = None
process_lock = Lock()


def cleanup_rtl_process():
    """Ensure that rtl_fm process is terminated on exit."""
    global rtl_process
    if rtl_process:
        try:
            os.killpg(os.getpgid(rtl_process.pid), signal.SIGTERM)
            rtl_process.wait()  # Wait for the process to terminate
            print("Cleaned up rtl_fm process on exit.")
        except Exception as e:
            print(f"Failed to kill rtl_fm process during cleanup: {e}")

# Register cleanup function to run on script exit
atexit.register(cleanup_rtl_process)

def start_rtl_fm(frequency='162.400M', gain=60):
    global rtl_process

    with process_lock:
        # Kill any previously running rtl_fm processes
        if rtl_process:
            try:
                os.killpg(os.getpgid(rtl_process.pid), signal.SIGTERM)  # Kill process group
                rtl_process.wait()  # Wait for the process to fully terminate
                print("Killed previous rtl_fm process.")
            except Exception as e:
                print(f"Failed to kill rtl_fm process: {e}")
            rtl_process = None  # Reset the rtl_process variable

        # Add a small delay to ensure the device is released
        time.sleep(1)

        # Start rtl_fm and pipe it to sox in a new process group
        rtl_command = f"rtl_fm -f {frequency} -M fm -s 24k -r 24k -g {gain} | sox -t raw -r 24000 -e signed-integer -b 16 -c 1 - -t wav -"
        try:
            rtl_process = subprocess.Popen(rtl_command, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
            print(f"Started rtl_fm with frequency={frequency} and gain={gain}")
        except Exception as e:
            rtl_process = None
            print(f"Failed to start rtl_fm: {e}")

def poll_server():
    server_url = "https://websocket-audio-server-883583974128.us-west1.run.app/config"
    global rtl_process

    current_frequency = '162.400M'
    current_gain = 60

    while True:
        try:
            # Poll for the latest configuration
            response = requests.get(server_url)
            if response.status_code == 200:
                data = response.json()
                new_frequency = data.get('frequency', current_frequency)
                new_gain = data.get('gain', current_gain)

                if new_frequency != current_frequency or new_gain != current_gain:
                    # If the frequency or gain has changed, update the RTL process
                    current_frequency = new_frequency
                    current_gain = new_gain
                    print("Got new settings from server")
                    start_rtl_fm(current_frequency, current_gain)
            else:
                print(f"Failed to get config from server: {response.status_code}")

        except requests.RequestException as e:
            print(f"Error polling server: {e}")

        time.sleep(5)  # Poll every 5 seconds (adjust as needed)

def on_open(ws):
    print("Connected to server for streaming")
    try:
        while True:
            with process_lock:
                process = rtl_process
            chunk = process.stdout.read(2048) if process else None
            if not chunk:
                print("No data from rtl_fm. Waiting to reconnect...")
                break
            ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print(f"Error streaming audio: {e}")

def on_message(ws, message):
    print(f"Message received: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: {close_status_code}, {close_msg}")

def start_websocket_streaming():
    websocket_url = "wss://websocket-audio-server-883583974128.us-west1.run.app"
    while True:
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

        print("Reconnecting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    # Start rtl_fm initially
    start_rtl_fm()

    # Start the polling process to check for updates to frequency/gain
    polling_thread = threading.Thread(target=poll_server)
    polling_thread.daemon = True  # Keep this thread running in the background
    polling_thread.start()

    # Start the WebSocket streaming
    start_websocket_streaming()
