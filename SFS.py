import os
from datetime import datetime
import socket
import threading
import time
import hashlib
import queue
import json
from tqdm import tqdm
import argparse

def validate_ip(s):
    try:
        socket.inet_aton(s)
        return s
    except socket.error:
        raise argparse.ArgumentTypeError(f"Invalid IP address: {s}")

# Step 2: Create an ArgumentParser object
parser = argparse.ArgumentParser(description="Process an IP address.")

# Step 3: Add arguments
parser.add_argument("--ip", help="The IP address to process.", type=validate_ip, required=False)

# Step 4: Parse arguments
args = parser.parse_args()


def hash_ip(ip_address, hash_func='sha256'):
    # Ensure ip_address is just the IP string, not a tuple
    if isinstance(ip_address, tuple):
        ip_address = ip_address[0]  # Select the IP address part of the tuple

    # Create a new hash object using the specified hash function
    hasher = hashlib.new(hash_func)
    # Update the hasher with the IP address, encoded to bytes
    hasher.update(ip_address.encode())
    # Return the hexadecimal digest of the hash
    return hasher.hexdigest()

def get_local_ip():
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use Google's public DNS server to determine the active interface
        # This does not actually create a connection
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def udp_discovery_listener(addr_remote):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', UDP_PORT))

    while True:
        message, addr = udp_socket.recvfrom(BUFFER_SIZE)
        if message.decode() == DISCOVERY_MESSAGE:

            # Respond to the discovery request
            udp_socket.sendto("DISCOVER_RESPONSE".encode(), addr)
            if addr[0] != get_local_ip():
                print(f"Discovery request received from {addr}")
                addr_remote.put(addr)
                return

def udp_discovery_broadcast():
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(DISCOVERY_MESSAGE.encode(), (BROADCAST_ADDRESS, UDP_PORT))
        print("Discovery request broadcasted.")
        time.sleep(0.5)
def tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 26214)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen(1)
    print("TCP server listening...")
    conn, addr = tcp_socket.accept()
    print(f"Connection established with {addr}")
    return   conn

def tcp_client(server_ip):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
    tcp_socket.connect((server_ip, TCP_PORT))
    print(f"Connected to {server_ip}")
    return  tcp_socket

import json
import socket

def send_json(sock, data):
    # Convert the data to JSON and then bytes
    message = json.dumps(data).encode()
    # Prepare the header
    header = f"{len(message):<10}".encode()
    # Send header + message
    sock.sendall(header + message)


def recv_json(sock):
    # Read the message length from the header
    header = b''
    while len(header) < 10:
        fragment = sock.recv(10 - len(header))
        if not fragment:
            raise Exception("Socket connection broken")
        header += fragment
    message_length = int(header.decode().strip())

    # Read the message data based on the length
    chunks = []
    bytes_recd = 0
    while bytes_recd < message_length:
        chunk = sock.recv(min(message_length - bytes_recd, 2048))
        if chunk == b'':
            raise RuntimeError("Socket connection broken")
        chunks.append(chunk)
        bytes_recd += len(chunk)
    message = b''.join(chunks).decode()

    return json.loads(message)


import os
import socket
import json


def send_file(conn, filepath, remaining_files):
    # Prepare file metadata
    filesize = os.path.getsize(filepath)
    metadata = {
        "filesize": filesize,
        "relative_path": filepath,  # Assume filepath is the relative path you want to send
        "remaining_files": remaining_files
    }

    # Send metadata as a JSON string
    metadata_str = json.dumps(metadata)
    conn.sendall(f"{len(metadata_str):<16}".encode() + metadata_str.encode())

    # Send the file in chunks
    bytes_sent = 0
    bytes_accumulated  = 0
    update_chunk_size = filesize / 500
    with open(filepath, 'rb') as f, tqdm(total=filesize, desc=f"Sending {os.path.basename(filepath)}", unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        while bytes_sent < filesize:
            chunk = f.read(4096)
            conn.sendall(chunk)
            bytes_sent += len(chunk)
            bytes_accumulated += len(chunk)
            if bytes_accumulated >= update_chunk_size:
                pbar.update(bytes_accumulated)
                bytes_accumulated = 0
    print(f"Sent {filepath}, {remaining_files} files remaining.")


import socket
import json


def recv_all(conn, length):
    """Helper function to ensure all data is received."""
    data = b''
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            raise Exception("Connection lost")
        data += packet
    return data

def receive_file(conn):
    # Receive the length of the metadata JSON string
    metadata_len_str = recv_all(conn, 16)
    metadata_len = int(metadata_len_str.decode().strip())

    # Receive the metadata JSON string
    metadata_str = recv_all(conn, metadata_len).decode()
    metadata = json.loads(metadata_str)

    # Extract metadata
    filesize = metadata['filesize']
    relative_path = metadata['relative_path']
    remaining_files = metadata['remaining_files']

    # Compute save path (ensure directories exist or create them)
    save_path = os.path.abspath(relative_path)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Receive the file data
    bytes_received = 0
    bytes_accumulated = 0
    update_chunk_size = filesize / 500
    with open(save_path, 'wb') as f, tqdm(total=filesize, desc=f"Receiving {os.path.basename(relative_path)}", unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        while bytes_received < filesize:
            chunk = recv_all(conn, min(filesize - bytes_received, 4096))
            f.write(chunk)
            bytes_received += len(chunk)
            bytes_accumulated += len(chunk)
            if bytes_accumulated >= update_chunk_size:
                pbar.update(bytes_accumulated)
                bytes_accumulated = 0

    print(f"Received {relative_path}, {remaining_files} files remaining.")

    return remaining_files


def sendDelta(isSever, socket, files_dict, remote_dict):
    delta_dict = dict()

    for file in files_dict:
        if not file in remote_dict:
            delta_dict[file] = files_dict[file]
        elif remote_dict[file] < files_dict[file]:
            #print(remote_dict[file],files_dict[file])
            delta_dict[file] = files_dict[file]

    print(delta_dict)

    files_send = 0;
    for file in delta_dict:
        files_send += 1
        send_file(socket, file, len(delta_dict) - files_send)


def recvDelta(socket):
    filesRemaining  = 1
    while filesRemaining > 0:
       filesRemaining = receive_file(socket)

class StoppableThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            udp_discovery_broadcast()
            time.sleep(1)
        print("Thread is stopping...")

# Configuration
UDP_PORT = 50000
TCP_PORT = 50001
BROADCAST_ADDRESS = '255.255.255.255'
DISCOVERY_MESSAGE = "DISCOVER_REQUEST"
BUFFER_SIZE = 1024


# Path to the directory you want to scan
directory_path = os.getcwd()

files_dict = dict()

# Loop through each file in the directory
# Walk through all directories and files in the directory
for root, dirs, files in os.walk(directory_path):
    #(f"Directory: {root}")
    for filename in files:

        # Get the full path of the file
        file_path = os.path.join(root, filename)
        file_path =os.path.relpath(file_path)

        if not os.path.isdir(os.path.abspath(file_path)):
            # Get the last modified time of the file
            last_modified_time = os.path. getmtime(os.path.abspath(file_path))
            files_dict[file_path] = last_modified_time

#print(len(files_dict))

if args.ip is None:
    addr_remote = queue.Queue()

    listener_thread = threading.Thread(target=udp_discovery_listener, args=(addr_remote,))
    listener_thread.start()

    #while listener_thread.is_alive():
    thread = StoppableThread()
    thread.start()

    listener_thread.join()

    ip_local = get_local_ip()
    ip_remote = addr_remote.get()[0]
else:
    ip_local = get_local_ip()
    ip_remote = args.ip

if hash_ip(ip_remote) > hash_ip(ip_local):
    socket = tcp_server()
    if args.ip is None:
        thread.stop()
        thread.join()
    #socket.send(json.dumps(files_dict).encode())
    send_json(socket, files_dict)
    #remote_files = json.loads(socket.recv(64000).decode())
    remote_files = recv_json(socket)
    #print(remote_files)
    sendDelta(isSever = True, socket= socket, files_dict= files_dict, remote_dict= remote_files)
    recvDelta(socket)
elif hash_ip(ip_remote) < hash_ip(ip_local):
    socket = tcp_client(ip_remote)
    if args.ip is None:
        thread.stop()
        thread.join()
    #remote_files = json.loads(socket.recv(64000).decode())
    remote_files = recv_json(socket)
    #print(remote_files)
    #socket.send(json.dumps(files_dict).encode())
    send_json(socket, files_dict)
    recvDelta(socket)
    sendDelta(isSever=False, socket= socket, files_dict= files_dict, remote_dict= remote_files)
else:
    print("ohoh")
