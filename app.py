CHUNK_SIZE = 16         # 16 KB
CACHE_SIZE = 25000      # 25 MB

## For each node's cache
class Cached_video:
     def __init__(self, id, my_chunks = [], total_chunks = 0):
          self.id = id
          self.my_chunks = my_chunks
          self.total_chunks = total_chunks

## Node class 
class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.peers = []
        self.cache = {}  # video cache: {video_id: {Cached_video}}


if __name__ == "__main__":
        print("Hello")