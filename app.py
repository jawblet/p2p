import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json
import random
import zlib

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video_Chunk, Video

## Node class 
class Node:
        def __init__(self):
                self.peers = []  # peer uids
                self.cache = {}  # video cache: {video_id: {chunk_id : Cached_Video_Chunk}}
                self.cache_space = CACHE_SIZE
                self.registered = False
                self.manifest = []
                self.video_chunk_to_peer = {} # video mapping: {video_uid : {chunk_id : [peer addr list]}}
                
                self.id = None
                self.port = random.randrange(1025, 60000)
                self.addr = ('127.0.0.1', self.port)
                self.sock = socket(AF_INET, SOCK_DGRAM) # udp socket
                self.sock.bind(self.addr)
                self.requests = []
                self.results = {}
              
        # wait for server response
        def wait_response(self, request_id):
                while request_id in n.requests:
                        time.sleep(.01)
                        
        def get_video(self, video_uid):
                self.request_server('GET_CHUNK_MAPPING', video_uid)
                for chunk_id, peer_list in self.video_chunk_to_peer[video_uid].items():
                        if peer_list == []:
                                # REQUEST VIDEO FROM SERVER
                                self.request_server('GET_CHUNK', video_uid, chunk_id)
                        else:
                                # REQUEST FROM PEERS
                                for peer in peer_list:
                                        self.request_peer('GET_CHUNK', video_uid, chunk_id, tuple(peer))

        # evict oldest item in cache
        def evict_cache(self):
                least_recently_added = min(self.cache.values(), key=lambda obj: obj["time_added"])
                evict_size = CHUNK_SIZE
                print("least recent: ", least_recently_added)
                del self.cache[least_recently_added.video_uid][least_recently_added.chunk_id]
                self.cache_space -= evict_size

        def cache_is_full(self):
                return self.cache_space <= 0

       
        # nodes should cache different pieces of video so there's balance
        # prioritize first part of video? 
        def add_to_cache(self, video_uid, chunk_id, data):
                if(self.cache_is_full()):
                        self.evict_cache()
              
                cache_entry = Cached_Video_Chunk(video_uid, chunk_id, data)
                self.cache[video_uid] = {chunk_id : cache_entry}
                #self.print_cache()

        # check if chunk is in my cache
        def lookup_in_cache(self, video_uid, chunk_id):
                if video_uid in self.cache.keys():
                        if chunk_id in self.cache[video_uid].keys():
                                return chunk_id
                        
                return None

        def print_cache(self):
              for video_uid in self.cache.keys():
                    print(video_uid, list(self.cache[video_uid].keys()), max(list(self.cache[video_uid].values().added)))
                    
        def request_server(self, request, video_uid=None, chunk_id=None):
              rid = str(uuid.uuid4())
              request = {'request': request, 'id': rid, 'video_uid': video_uid, 'chunk_id': chunk_id}
              print(f'{self.addr}: {request}')
              request_data = json.dumps(request).encode()
              
              self.requests.append(rid)
              
              self.sock.sendto(request_data, SERVER_ADDR)
              
              self.wait_response(rid)
              
              return rid

              
        def request_peer(self, request, video_uid, chunk_id, peer_addr):
              rid = str(uuid.uuid4())
              request = {'request': request, 'id': rid, 'video_uid': video_uid, 'chunk_id': chunk_id}
              print(f'{self.addr}: {request}')
              request_data = json.dumps(request).encode()
              
              self.requests.append(rid)
              
              self.sock.sendto(request_data, peer_addr)
              
              self.wait_response(rid)
              
              return rid
        
        # handle all requests/response   
        def handle(self, data, addr):
                # check if server response
                if addr == SERVER_ADDR:
                        response = json.loads(zlib.decompress(data).decode())
                        print(f'{addr}: {response}')
                        match response['request']:
                                # check if registration was successful
                                case 'REGISTER':
                                        self.registered = True
                                        self.id = response['data']
                                # check if response to manifest request
                                case 'GET_MANIFEST':
                                        self.manifest = response['data']
                                # check if response to chunk mapping request
                                case 'GET_CHUNK_MAPPING':
                                        self.video_chunk_to_peer[response['video_uid']] = response['data']
                                # check if response to chunk request
                                case 'GET_CHUNK':
                                        if self.lookup_in_cache(response['video_uid'], response['chunk_id']) == None:
                                                self.add_to_cache(response['video_uid'], response['chunk_id'], response['data'])
                                        
                        self.requests.remove(response['id'])
                        self.results[response['id']] = response['data']
                
                # else, request/response from peer
                else:
                        tmp = json.loads(data.decode())
                        
                        # check if response to request
                        if tmp['id'] in self.requests:
                                response = tmp

                                self.requests.remove(response['id'])
                                self.results[response['id']] = response['data']
                        # else is request
                        else:
                                request = tmp
                                

                        print(f'{addr}: {data}')
            
        
        # listen for peer/server requests/response    
        def listen(self):
                while True:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        request_thread = Thread(target=self.handle, daemon=True, args=(data, addr,))
                        request_thread.start()

if __name__ == "__main__":
        n = Node()
        listen_thread = Thread(target=n.listen, daemon=True, args=())
        listen_thread.start()
        n.request_server('REGISTER') 
        n.request_server('GET_MANIFEST')
                
        # GET CERTAIN VIDEO
        video_uid = n.manifest[0]
        n.get_video(video_uid)
        
        while 1:
          time.sleep(1)
                        
        # DEREGISTER
        #n.request_server('DEREGISTER')