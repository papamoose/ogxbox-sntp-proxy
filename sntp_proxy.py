#!/usr/bin/env python3
import socket
import struct
import time
import argparse
from collections import defaultdict
from datetime import datetime, timezone

# Define the NTP server to use for time synchronization
NTP_SERVER = "192.168.1.1"
NTP_PORT = 123
SNTP_PORT = 37

# Dictionary to track request counts
request_counts = defaultdict(int)
last_request_time = defaultdict(int)
RATE_LIMIT_PERIOD = 60  # 60 seconds for rate limiting
MAX_REQUESTS_PER_PERIOD = 2  # Allow a maximum of 5 requests per period

# Predefined invalid timestamp to send in case of rate-limiting or error
INVALID_TIMESTAMP = 0xFFFFFFFF  # Max value for a 4-byte unsigned integer

def get_ntp_time(debug=False):
  """Fetch time from an NTP server."""
  client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client.settimeout(5)
  NTP_PACKET = b'\x1b' + 47 * b'\0'

  try:
    client.sendto(NTP_PACKET, (NTP_SERVER, NTP_PORT))
    response, _ = client.recvfrom(1024)

    if debug:
      print(f"DEBUG: Raw NTP response: {response}")

    # Check if the response contains the string "RATE", indicating a rate-limiting error
    if b"RATE" in response:
      print("Received rate-limiting response from the NTP server. Skipping...")
      return None

    unpacked = struct.unpack('!12I', response)
    timestamp = unpacked[10]
    if debug:
      print(f"DEBUG: Timestamp unpacked: {timestamp}")
    unix_time = timestamp - 2208988800  # Convert to Unix timestamp
    return unix_time

  except Exception as e:
    print(f"Error getting NTP time: {e}")
    return None
  finally:
    client.close()


def is_rate_limited(client_address, debug=False):
  """Check if the client is exceeding the allowed request rate."""
  current_time = time.time()

  # Use only the IP address (client_address[0]) to track rate-limiting
  client_ip = client_address[0]

  # Initialize last_request_time if it's the first request for this client
  if client_ip not in last_request_time:
    last_request_time[client_ip] = current_time
    request_counts[client_ip] = 0  # Initialize the request count to 1 for the first request

  # Reset the count if the period has elapsed
  if current_time - last_request_time[client_ip] > RATE_LIMIT_PERIOD:
    request_counts[client_ip] = 0  # Reset the count to 1 after the period (first request in new period)

  # Update the last request time and increment the request count
  last_request_time[client_ip] = current_time
  request_counts[client_ip] += 1

  print(f"{client_address[0]} | req_count: {request_counts[client_ip]} | currtime: {current_time} | lastreqtime: {last_request_time[client_ip]}")

  return request_counts[client_ip] > MAX_REQUESTS_PER_PERIOD


def proxy_sntp_to_ntp(debug=False):
    """Proxy SNTP requests on port 37 to an NTP server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', SNTP_PORT))

    print(f"Listening for SNTP requests on port {SNTP_PORT}...")

    while True:
      data, client_address = server_socket.recvfrom(1024)
      print(f"{client_address[0]} | Received SNTP request from {client_address}")

      # Combined condition to check rate limiting or invalid NTP time
      ntp_time = get_ntp_time(debug)

      if is_rate_limited(client_address, debug) or ntp_time is None or ntp_time < 0 or ntp_time > 4_294_967_295:
        print(f"{client_address[0]} | Failed to get valid NTP time or rate limit exceeded for client {client_address}. Sending invalid timestamp.")
        # Send the invalid timestamp to the client
        response = struct.pack('!I', INVALID_TIMESTAMP)
        server_socket.sendto(response, client_address)
        continue  # Immediately continue to the next request without further processing

      try:
        # Pack the NTP time into the SNTP response (4 bytes)
        response = struct.pack('!I', ntp_time)
        # Send the SNTP response back to the client
        server_socket.sendto(response, client_address)
        # Convert the Unix timestamp to ISO 8601 format for logging
        iso_time = datetime.fromtimestamp(ntp_time, timezone.utc).isoformat()
        print(f"{client_address[0]} | Sent SNTP response to {client_address} with time {ntp_time} (ISO 8601: {iso_time})")
      except struct.error as e:
        print(f"{client_address[0]} | Error packing response: {e}")


if __name__ == "__main__":
  # Set up argument parser
  parser = argparse.ArgumentParser(description="Proxy SNTP to NTP with rate limiting and debug options.")
  parser.add_argument('--debug', action='store_true', help="Enable debug output")

  # Parse arguments
  args = parser.parse_args()

  # Run the proxy with debug mode based on the argument
  proxy_sntp_to_ntp(debug=args.debug)
