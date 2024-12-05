import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread, Lock
import json
import random
import zlib

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, START_UP, Cached_Video_Chunk, Video

## Node class 
class Node:
        def __init__(self, log_file, latency, bandwidth):
                self.peers = []  # peer addrs
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
                self.log_file = log_file
                self.latency = float(latency)
                self.bandwidth = int(bandwidth)
                
                self.lock = Lock()
                
                listen_thread = Thread(target=self.listen, daemon=True, args=())
                listen_thread.start()
                
                self.request_server('REGISTER') 
                self.request_server('GET_MANIFEST')
                self.request_server('GET_PEERS')
        
        def log_stats(self, playback_latency, rebuffering_time):
                with open(self.log_file, 'a') as log:
                        log.write(f'{time.time()}|{self.addr}|{playback_latency}|{rebuffering_time}\n')
        
        # get delay of tranmission
        def get_delay(self, size):
                bandwidth = int(random.gauss(self.bandwidth, .1 * self.bandwidth))
                latency = int(random.gauss(self.latency, .1 * self.latency))
                
                return (size / bandwidth) + latency
                        
        # wait for server response
        def wait_response(self, request_id):
                while request_id in self.requests:
                        time.sleep(.01)
        
        def get_video_chunk(self, video_uid, chunk_id, peer_addr=None):
                if not peer_addr:
                        self.request_server('GET_CHUNK', video_uid, chunk_id) 
                else:
                        self.request_peer('GET_CHUNK', video_uid, chunk_id, peer_addr)
               
        def get_video(self, video_uid):
                st = time.time()
                self.request_server('GET_CHUNK_MAPPING', video_uid)
                size = self.video_chunk_to_peer[video_uid]['size']
                for chunk_id, peer_list in self.video_chunk_to_peer[video_uid]['chunks'].items():
                        if peer_list == []:
                                # REQUEST VIDEO FROM SERVER
                                chunk_thread = Thread(target=self.get_video_chunk, daemon=True, args=(video_uid, chunk_id,))
                                chunk_thread.start()
                        else:
                                # REQUEST FROM PEERS
                                for peer in peer_list:
                                        chunk_thread = Thread(target=self.get_video_chunk, daemon=True, args=(video_uid, chunk_id, tuple(peer),))
                                        chunk_thread.start()
                                
                
                buffer = 0
                curr_chunk_id = 0
                upt = None
                rebuffer = 0
                while video_uid not in self.cache.keys() or len(self.cache[video_uid]) < size / CHUNK_SIZE:
                        time.sleep(.01)
                        if self.lookup_in_cache(video_uid, str(curr_chunk_id)):
                                if curr_chunk_id == START_UP:
                                        upt = time.time()
                                        curr_chunk_id += CHUNK_SIZE
                                        buffer += 1
                                        #print('got chunk: ', curr_chunk_id)
                        if upt != None:
                                buffer -= .01
                                if buffer < 0:
                                        rebuffer += .01
                
                if upt == None:
                        upt = time.time()
                self.log_stats(upt-st, rebuffer)
                        
                           

        # evict oldest item in cache
        def evict_cache(self):
                least_recently_added_video = None
                least_recently_added_chunk = None
                least_recently_added_time = None
                for video_uid, chunks in self.cache.items():
                        for chunk_id, chunk in chunks.items():
                                if not least_recently_added_time or chunk.added < least_recently_added_time:
                                        least_recently_added_video = video_uid
                                        least_recently_added_chunk = chunk_id
                                        least_recently_added_time = chunk.added

                del self.cache[least_recently_added_video][least_recently_added_chunk]

                self.cache_space -= CHUNK_SIZE

        def cache_is_full(self):
                return self.cache_space <= 0

        # nodes should cache different pieces of video so there's balance
        # prioritize first part of video? 
        def add_to_cache(self, video_uid, chunk_id, data):
                if(self.cache_is_full()):
                        self.evict_cache()
              
                cache_entry = Cached_Video_Chunk(video_uid, chunk_id, data)
                if video_uid not in self.cache.keys():
                        self.cache[video_uid] = {}
                self.cache[video_uid][chunk_id] = cache_entry
                #self.print_cache()

        # check if chunk is in my cache
        def lookup_in_cache(self, video_uid, chunk_id):
                if video_uid in self.cache.keys():
                        if chunk_id in self.cache[video_uid].keys():
                                return self.cache[video_uid][chunk_id]
                        
                return None

        def print_cache(self):
              print(self.cache)
                    
        def request_server(self, request, video_uid=None, chunk_id=None):
              rid = str(uuid.uuid4())
              request = {'request': request, 'id': rid, 'video_uid': video_uid, 'chunk_id': chunk_id}
              print(f'{self.addr}: {request}')
              request_data = json.dumps(request).encode()
              
              self.requests.append(rid)
              
              time.sleep(self.get_delay(len(request_data))) 
              
              self.sock.sendto(request_data, SERVER_ADDR)
              
              self.wait_response(rid)
              
              return rid

              
        def request_peer(self, request, video_uid, chunk_id, peer_addr):
              rid = str(uuid.uuid4())
              request = {'request': request, 'id': rid, 'video_uid': video_uid, 'chunk_id': chunk_id}
              print(f'{self.addr}: {request}')
              request_data = json.dumps(request).encode()
              self.requests.append(rid)
              time.sleep(self.get_delay(len(request_data))) 
              self.sock.sendto(request_data, peer_addr)
              self.wait_response(rid)
              
              return rid
        
        # handle all requests/response   
        def handle(self, data, addr):
                with self.lock:
                        # check if server response
                        if addr == SERVER_ADDR:
                                response = json.loads(zlib.decompress(data).decode())
                                #print(f'{addr}: {response}')
                                # print(f'{addr}: {response}')
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
                                        # check if peers
                                        case 'GET_PEERS':
                                                self.peers = response['data']

                                self.requests.remove(response['id'])
                                self.results[response['id']] = response['data']
                        
                        # else, request/response from peer
                        else:
                                tmp = json.loads(data.decode())
                                #print(f'{addr}: {tmp}')
                                
                                # check if response to request
                                if tmp['id'] in self.requests:
                                        response = tmp
                                        if self.lookup_in_cache(response['video_uid'], response['chunk_id']) == None and response['data'] != 'ERROR':
                                                        self.add_to_cache(response['video_uid'], response['chunk_id'], response['data'])
                                        self.requests.remove(response['id'])
                                        try:
                                                self.results[response['id']] = response['data']
                                        except:
                                                pass
                                # else is request
                                else:
                                        request = tmp
                                        response = {'request': request['request'], 'id': request['id']}
                                        chunk = self.lookup_in_cache(request['video_uid'], request['chunk_id'])
                                        if chunk != None:
                                              response['video_uid'] = chunk.video_uid
                                              response['chunk_id'] = chunk.chunk_id
                                              response['data'] = chunk.data
                                        else:
                                              response['data'] = 'ERROR'
                                              
                                        response_data = json.dumps(response).encode()
                                        time.sleep(self.get_delay(len(response_data) + CHUNK_SIZE)) 
                                        self.sock.sendto(response_data, addr)  
                                        #print(f'{addr}: {response}')

            
        
        # listen for peer/server requests/response    
        def listen(self):
                while True:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        request_thread = Thread(target=self.handle, daemon=True, args=(data, addr,))
                        request_thread.start()

        def get_random_video(self):
              self.get_video(random.choice(self.manifest))
        
if __name__ == "__main__":
        n = Node('log.txt')
        v = Video()
        # n.add_to_cache()

        listen_thread = Thread(target=n.listen, daemon=True, args=())
        listen_thread.start()
        n.request_server('REGISTER') 
        n.request_server('GET_MANIFEST')
        n.request_server('GET_PEERS')
                
        # GET CERTAIN VIDEO
        video_uid = n.manifest[0]
        n.get_video(video_uid)
        
        while 1:
          time.sleep(1)
                        
        # DEREGISTER
        n.request_server('DEREGISTER')