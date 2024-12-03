import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video, Video

class Server:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.peers = []  # peer uids
                self.chunk_mapping = {} # video mapping: {video_id : {chunk_id : [peer list]}}
                self.chunks = {}  # video chunks: {video_id: [chunk_id list]}
                self.sock = socket(AF_INET, SOCK_DGRAM) #udp socket
                self.sock.bind(SERVER_ADDR)

        
        # handle peer connection 
        def handle_request(self, data, addr):
                request = json.loads(data.decode())
                print(request)
                print(addr)
              
        # listen for peer request    
        def listen(self):
                while True:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        request_thread = Thread(target=self.handle_request, daemon=True, args=(data, addr,))
                        request_thread.start()
        
        # register peer
        def register_peer(self):
                pass
              
              
if __name__ == "__main__":
        s = Server()
        s.listen()