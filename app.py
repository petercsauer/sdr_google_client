from flask import Flask, request, jsonify
from subprocess import Popen, PIPE
import os
import signal

app = Flask(__name__)

# Global variable to store the rtl_fm process
rtl_fm_process = None

def start_rtl_fm(frequency):
    global rtl_fm_process
    # If a process is already running, kill it
    if rtl_fm_process:
        os.killpg(os.getpgid(rtl_fm_process.pid), signal.SIGTERM)

    # Start a new rtl_fm process with the given frequency
    cmd = f"rtl_fm -f {frequency}M -M fm -s 24k -r 24k -g 35 - | sox -t raw -r 24000 -e signed-integer -b 16 -c 1 - -t wav - | python3 transcribe.py"
    rtl_fm_process = Popen(cmd, shell=True, preexec_fn=os.setsid)

@app.route('/set_frequency', methods=['POST'])
def set_frequency():
    data = request.get_json()
    frequency = data.get('frequency')
    if not frequency:
        return jsonify({"error": "Please provide a frequency"}), 400

    try:
        start_rtl_fm(frequency)
        return jsonify({"message": f"Frequency changed to {frequency} MHz"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Start the initial rtl_fm process
    start_rtl_fm(100.3)  # Default frequency at startup
    app.run(host='0.0.0.0', port=5000)
