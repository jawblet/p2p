import time
import uuid
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import json

from common import CACHE_SIZE, CHUNK_SIZE, SERVER_ADDR, BUFFER_SIZE, Cached_Video, Video

## Node class 
class Node:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.peers = []  # peer uids
                self.cache = {}  # video cache: {video_id: {Cached_video}}
                self.cache_space = CACHE_SIZE
                self.sock = socket(AF_INET, SOCK_DGRAM) # udp socket


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
                    
        def request_server(self):
              request = {'request': 'GET_MANIFEST'}
              
              request_data = json.dumps(request).encode()
              
              self.sock.sendto(request_data, SERVER_ADDR)
              
              response_data, _ = self.sock.recvfrom(BUFFER_SIZE)
              
              response = json.loads(response_data.decode())
              
              print(response)
              
              



if __name__ == "__main__":
        v = Video()
        n = Node()
        n.add_to_cache(v)
        n.print_cache()
        
        n.request_server()
        
        print("Hello")