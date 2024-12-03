import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json
import random

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video, Video

## Node class 
class Node:
        def __init__(self):
                self.peers = []  # peer uids
                self.cache = {}  # video cache: {video_id: {Cached_video}}
                self.cache_space = CACHE_SIZE
                self.register = False
                
                
                self.port = random.randrange(1025, 60000)
                self.addr = ('127.0.0.1', self.port)
                self.sock = socket(AF_INET, SOCK_DGRAM) # udp socket
                self.sock.bind(self.addr)


        # evict oldest item in cache
        def evict_cache(self):
                least_recently_added = min(self.cache.values(), key=lambda obj: obj["time_added"])
                evict_size = least_recently_added.my_chunks * CHUNK_SIZE
                print("least recent: ", least_recently_added)
                del self.cache[least_recently_added.id]
                self.cache_space -= evict_size

        def cache_is_full(self):
                return self.cache_space <= 0

       
        # nodes should cache different pieces of video so there's balance
        # prioritize first part of video? 
        def add_to_cache(self, video):
                if(self.cache_is_full()):
                        self.evict_cache()
                
                cache_entry = Cached_Video(video.uid, [0])

                self.cache[video.uid] = cache_entry
                self.print_cache()


        def print_cache(self):
              for chunk in self.cache.values():
                    print(chunk.id, chunk.my_chunks, chunk.added)
                    
        def request_server(self, op):
              request = {'request': op, 'id': str(uuid.uuid4())}
              
              print(f'{self.addr}: {request}')
              
              request_data = json.dumps(request).encode()
              
              self.sock.sendto(request_data, SERVER_ADDR)

              
        def request_peer(self):
              pass
        
        # handle all requests/response   
        def handle(self, data, addr):
              # check if server response
              if addr == SERVER_ADDR:
                      response = json.loads(data.decode())
                      print(f'{addr}: {response}')
              # else, something from peer
              else:
                      pass
        
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
        time.sleep(5)
        n.request_server('DEREGISTER')
        time.sleep(5)