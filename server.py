import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video, Video

class Server:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.peers = []  # peer addrs
                self.chunk_mapping = {} # video mapping: {video_id : {chunk_id : [peer addr list]}}
                self.chunks = {}  # video chunks: {video_id: [chunk_id list]}
                self.sock = socket(AF_INET, SOCK_DGRAM) #udp socket
                self.sock.bind(SERVER_ADDR)

        def bootstrap(self):
                for _ in range(0,10):
                        v = Video()
                        self.chunks[v.uid] = {}
        
        # handle peer request 
        def handle_request(self, request_data, addr):
                request = json.loads(request_data.decode())
                print(f'{addr}: {request}')
                
                # register peer
                if request['request'] == 'REGISTER':
                        if addr not in self.peers:
                                self.peers.append(addr)
                        response = {'request': request['request'], 'id': request['id'], 'status': 'DONE'}
                elif request['request'] == 'DEREGISTER':
                        if addr in self.peers:
                                self.peers.remove(addr)
                        response = {'request': request['request'], 'id': request['id'], 'status': 'DONE'}
                        
                # respond to peer
                data = json.dumps(response).encode()
                self.sock.sendto(data, addr)                             
              
        # listen for peer requests    
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
        s.bootstrap()
        s.listen()