"""
    Assigment for U8 A1: Concurrencia

    Author: Eloy Uziel García Cisneros (eloy.garcia@edu.uag.mx)

    usage: python server.py

    repo: https://github.com/uzielgc/uag_u8a1-concurrencia

    REF: https://pyshine.com/How-to-send-audio-video-of-MP4-using-sockets-in-Python/
"""

# Standard imports
import socket
import os
import base64
import threading
import pickle
import struct
import logging

# Third-party
import cv2
import numpy as np
import pyaudio

logging.basicConfig(level='INFO')
LOGGER = logging.getLogger(__name__)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))



BUFF_SIZE = 65536

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
host_name = socket.gethostname()
host_ip = '127.0.0.1'

port = 20001
client_socket.sendto(b'Starting conn.',(host_ip,port))

def audio_stream():
    p = pyaudio.PyAudio()
    CHUNK = 1024
    stream = p.open(format=p.get_format_from_width(2),
    				channels=2,
    				rate=44100,
    				output=True,
    				frames_per_buffer=CHUNK)

    client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socket_address = (host_ip,port-1)
    LOGGER.info('server listening at %s', socket_address)
    client_socket.connect(socket_address) 
    LOGGER.info("CLIENT CONNECTED TO %s", socket_address)
    data = b""
    payload_size = struct.calcsize("Q")
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024) # 4K
                if not packet: break
                data+=packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data  = data[msg_size:]
            frame = pickle.loads(frame_data)
            stream.write(frame)
        except:
            break

    client_socket.close()
    os._exit(1)
    
if __name__ == '__main__':
    label = "Receiving video"
    threading.Thread(target=audio_stream, args=()).start()

    cv2.namedWindow(label)        
    cv2.moveWindow(label, 250, 30) 

    while True:
        packet,_ = client_socket.recvfrom(BUFF_SIZE)
        data = base64.b64decode(packet,' /')
        npdata = np.fromstring(data,dtype=np.uint8)

        frame = cv2.imdecode(npdata,1)
        cv2.imshow(label,frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            client_socket.close()
            break

    client_socket.close()
    cv2.destroyAllWindows() 
