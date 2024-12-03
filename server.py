import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json
import random

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video, Video

class Server:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.peers = []  # peer addrs
                self.video_chunk_to_peer = {} # video mapping: {video_uid : {chunk_id : [peer addr list]}}
                self.video_to_chunk = {}  # video chunks: {video_uid: [chunk_id list]}
                self.sock = socket(AF_INET, SOCK_DGRAM) #udp socket
                self.sock.bind(SERVER_ADDR)

        def bootstrap(self):
                for _ in range(0,10):
                        v = Video()
                        self.video_to_chunk[v.uid] = v.chunks
                        self.video_chunk_to_peer[v.uid] = {}                        
                        for c in v.chunks:
                                self.video_chunk_to_peer[v.uid][c] = []
                print(self.video_to_chunk)
                print(self.video_chunk_to_peer)
        
        # handle peer request 
        def handle_request(self, request_data, addr):
                request = json.loads(request_data.decode())
                print(f'{addr}: {request}')
                
                response = {'request': request['request'], 'id': request['id']}
                
                match request['request']:
                        # register peer
                        case 'REGISTER':
                                if addr not in self.peers:
                                        self.peers.append(addr)
                                response['data'] = 'DONE'
                        # deregister peer
                        case 'DEREGISTER':
                                if addr in self.peers:
                                        self.peers.remove(addr)
                                response['data'] = 'DONE'
                        # get full video list
                        case 'GET_MANIFEST':
                                response['data'] = list(self.video_to_chunk.keys())
                        # get full peer list
                        case 'GET_PEERS':
                                response['data'] = self.peers
                        # get mapping from video to 
                        case 'GET_CHUNK_MAPPING':
                                response['data'] = self.video_chunk_to_peer[request['video_uid']]
                        case 'GET_CHUNK':
                                response['data'] = 'DATA'
                        case _:
                                response['data'] = 'ERROR'
                        
                # respond to peer
                data = json.dumps(response).encode()
                self.sock.sendto(data, addr)                             
              
        # listen for peer requests    
        def listen(self):
                while True:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        request_thread = Thread(target=self.handle_request, daemon=True, args=(data, addr,))
                        request_thread.start()
              
              
if __name__ == "__main__":
        s = Server()
        s.bootstrap()
        s.listen()