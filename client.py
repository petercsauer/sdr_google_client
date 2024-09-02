import sys
import websocket
import uuid

def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ':'.join([mac[e:e+2] for e in range(0, 11, 2)])

def on_message(ws, message):
    print(f"Received: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    # Send MAC address first
    mac_address = get_mac_address()
    ws.send(mac_address)
    print(f"Sent MAC address: {mac_address}")
    
    # Then send the audio stream
    print("Sending audio stream...")
    while True:
        chunk = sys.stdin.buffer.read(512)
        if not chunk:
            break
        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)

if __name__ == "__main__":
    websocket_url = "wss://your-server-url"
    ws = websocket.WebSocketApp(websocket_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

