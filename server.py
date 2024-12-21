import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread, Lock
import json
import random
import zlib
import sys

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Video

class Server:
        def __init__(self, log_file, latency, bandwidth, nvids):
                self.uid = uuid.uuid4()
                self.peers = []  # peer addrs
                self.video_chunk_to_peer = {} # video mapping: {video_uid : {chunk_id : [peer addr list]}}
                self.video_to_chunk = {}  # video chunks: {video_uid: [chunk_id list]}
                
                self.sock = socket(AF_INET, SOCK_DGRAM) #udp socket
                self.sock.bind(SERVER_ADDR)
                
                self.log_file = log_file
                self.latency = float(latency)
                self.bandwidth = int(bandwidth)
                self.lock = Lock()
                self.nvids = nvids
                
                self.bootstrap()
                self.listen()
        
        def bootstrap(self):
                with self.lock:
                        for _ in range(0,self.nvids):
                                v = Video()
                                self.video_to_chunk[v.uid] = v.chunks
                                self.video_chunk_to_peer[v.uid] = {}
                                self.video_chunk_to_peer[v.uid]['size'] = v.size
                                self.video_chunk_to_peer[v.uid]['chunks'] = {}                    
                                for chunk_id in v.chunks:
                                        self.video_chunk_to_peer[v.uid]['chunks'][str(chunk_id)] = []
        
        def log_stats(self, peer_addr, size):
                with open(self.log_file, 'a') as log:
                        log.write(f'{time.time()}|{SERVER_ADDR}|{peer_addr}|{size}\n')
        
        # get delay of tranmission
        def get_delay(self, size):
                bandwidth = int(random.gauss(self.bandwidth, .1 * self.bandwidth))
                latency = int(random.gauss(self.latency, .1 * self.latency))
                
                return (size / bandwidth) + latency
              
        # handle peer request 
        def handle_request(self, request_data, addr):
                with self.lock:
                        request = json.loads(request_data.decode())
                        #print(f'{addr}: {request}')
                        
                        response = {'request': request['request'], 'id': request['id']}
                        
                        match request['request']:
                                # register peer
                                case 'REGISTER':
                                        if addr not in self.peers:
                                                self.peers.append(addr)
                                        response['data'] = len(self.peers) - 1
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
                                        response['video_uid'] = request['video_uid']
                                        response['data'] = self.video_chunk_to_peer[request['video_uid']]
                                case 'GET_CHUNK':
                                        if len(self.video_chunk_to_peer[request['video_uid']]['chunks'][request['chunk_id']]) > 4:
                                                self.video_chunk_to_peer[request['video_uid']]['chunks'][request['chunk_id']] = self.video_chunk_to_peer[request['video_uid']]['chunks'][request['chunk_id']][1:]
                                        self.video_chunk_to_peer[request['video_uid']]['chunks'][request['chunk_id']].append(addr)
                                        response['video_uid'] = request['video_uid']
                                        response['chunk_id'] = request['chunk_id']
                                        response['data'] = 'DATA'
                                case _:
                                        response['data'] = 'ERROR'
                                
                        # respond to peer
                        data = zlib.compress(json.dumps(response).encode())
                        if response['request'] == 'GET_CHUNK':
                                time.sleep(self.get_delay(len(data) + CHUNK_SIZE)) 
                                self.log_stats(addr, len(data) + (CHUNK_SIZE * 1000))
                        else:
                                time.sleep(self.get_delay(len(data)))
                                self.log_stats(addr, len(data)) 
                        self.sock.sendto(data, addr)               
              
        # listen for peer requests    
        def listen(self):
                #print('LISTENING FOR PEERS')
                while True:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        request_thread = Thread(target=self.handle_request, daemon=True, args=(data, addr,))
                        request_thread.start()
              
              
if __name__ == "__main__":
        s = Server(sys.argv[1], sys.argv[2], sys.argv[3])
        s.bootstrap()
        s.listen()