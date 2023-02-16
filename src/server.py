"""
    Assigment for U8 A1: Concurrencia

    Author: Eloy Uziel García Cisneros (eloy.garcia@edu.uag.mx)

    usage: python server.py

    repo: https://github.com/uzielgc/uag_u8a1-concurrencia

    REF: https://pyshine.com/How-to-send-audio-video-of-MP4-using-sockets-in-Python/
"""

# Standard imports
import socket
import base64
import threading
import wave
import pickle
import struct
import queue
import os
import cv2
import imutils
import logging

logging.basicConfig(level='INFO')
LOGGER = logging.getLogger(__name__)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


# COST
QUEUE = queue.Queue(maxsize=10)
BUFF_SIZE = 65536
HOST = '127.0.0.1'
PORT = 20001

def get_video_info(vid: cv2.VideoCapture):
    fps = vid.get(cv2.CAP_PROP_FPS)

    LOGGER.info('FPS: %d', fps)
    total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_duration = float(total_frames) / float(fps)
    LOGGER.info("Video lenght: %d", vid_duration)
    return 1/fps

def preproc_vid(file_name):
    base_dir = os.path.dirname(file_name)
    base_name = os.path.splitext(os.path.basename(filename))[0]
    audiofile = f"{base_name}.wav"
    audiofile = os.path.join(base_dir, audiofile)
    if not os.path.exists(audiofile):
        command = f"ffmpeg -i {filename} -ab 160k -ac 2 -ar 44100 -vn {audiofile}"
        os.system(command)
    return audiofile

def video_stream_gen(vid):
    while(vid.isOpened()):
        try:
            _,frame = vid.read()
            frame = imutils.resize(frame, height=400)
            QUEUE.put(frame)
        except:
            os._exit(1)
    vid.release()

def audio_stream(audio_file):
    s = socket.socket()
    s.bind((HOST, (PORT-1)))

    s.listen(5)
    CHUNK = 1024
    wf = wave.open(audio_file, 'rb')
    LOGGER.info('server listening at %s',(HOST, (PORT-1)))
    client_socket,addr = s.accept()
    while True:
        if client_socket:
            while True:
                data = wf.readframes(CHUNK)
                a = pickle.dumps(data)
                message = struct.pack("Q",len(a))+a
                client_socket.sendall(message)

if __name__ == '__main__':

    label = "Streaming video"

    filename =  os.path.join(PROJECT_DIR, 'data', 'video.MP4')
    audio_file = preproc_vid(file_name=filename)

    LOGGER.info("%s, %s", filename, audio_file)

    vid = cv2.VideoCapture(filename)
    TS = get_video_info(vid=vid)

    threading.Thread(target=audio_stream, args=(audio_file,), daemon=True).start()
    threading.Thread(target=video_stream_gen, args=(vid,), daemon=True).start()

    cv2.namedWindow(label)        
    cv2.moveWindow(label, 10,30) 

    server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
    socket_address = (HOST, PORT)
    server_socket.bind(socket_address)
    LOGGER.info('Listening at: %s', socket_address)
    
    msg,client_addr = server_socket.recvfrom(BUFF_SIZE)
    LOGGER.info('GOT connection from %s', client_addr)
    while True:
            frame = QUEUE.get()
            encoded,buffer = cv2.imencode('.jpeg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])

            # Encode data
            message = base64.b64encode(buffer)
            server_socket.sendto(message,client_addr)
            
            cv2.imshow(label, frame)
            key = cv2.waitKey(int(1000*TS)) & 0xFF	
            if key == ord('q'):
                break	
