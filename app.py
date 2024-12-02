import time
import uuid

CHUNK_SIZE = 64         # 64 KB
CACHE_SIZE = 125000     # 125 MB
MAX_TT_SIZE = 287600    # 287.6 MB
AVG_TT_SIZE = 22000     # 22 MB = average size of 35s video, 1080p, 5 Mbps bitrate

## Full video
class Video:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.size = AVG_TT_SIZE

## Part of video that lives in node's cache
class Cached_video:
        def __init__(self, id, my_chunks = []):
                self.id = id
                self.my_chunks = my_chunks
                self.added = time.time()

## Node class 
class Node:
        def __init__(self):
                self.uid = uuid.uuid4()
                self.peers = []  # peer uids
                self.cache = {}  # video cache: {video_id: {Cached_video}}
                self.cache_space = CACHE_SIZE

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
                
                cache_entry = Cached_video(video.uid, [0])

                self.cache[video.uid] = cache_entry
                self.print_cache()


        def print_cache(self):
              for chunk in self.cache.values():
                    print(chunk.id, chunk.my_chunks, chunk.added)


if __name__ == "__main__":
        v = Video()
        n = Node()
        n.add_to_cache(v)
        n.print_cache()
        
        print("Hello")