#!/usr/bin/env python3
import socket
import struct
from datetime import datetime, UTC

# Address of your SNTP proxy (localhost in this case)
SNTP_SERVER = '192.168.1.1'
# SNTP port
SNTP_PORT = 37

def send_sntp_request():
  """Send an SNTP request to the proxy server."""
  client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client_socket.settimeout(5)  # Timeout for the request

  # SNTP request packet (4 bytes)
  sntp_request = b'\x00' * 4

  try:
    # Send the SNTP request to the proxy server
    client_socket.sendto(sntp_request, (SNTP_SERVER, SNTP_PORT))

    # Receive the SNTP response
    response, _ = client_socket.recvfrom(1024)

    # Unpack the response (assuming it's 4 bytes - Unix timestamp)
    unpacked = struct.unpack('!I', response)
    unix_time = unpacked[0]

    # Convert Unix timestamp to ISO 8601 format
    iso_time = datetime.fromtimestamp(unix_time)

    print(f"Received SNTP response: {unix_time} (Unix timestamp)")
    print(f"Converted to ISO 8601: {iso_time}")

  except Exception as e:
    print(f"Error: {e}")

  finally:
    client_socket.close()

if __name__ == "__main__":
  send_sntp_request()
