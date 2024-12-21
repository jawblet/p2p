import time
import uuid
import random

CHUNK_SIZE = 628         # 628 KB
CACHE_SIZE = 125000     # 125 MB
MAX_TT_SIZE = 287600    # 287.6 MB
AVG_TT_SIZE = 22000     # 22 MB = average size of 35s video, 1080p, 5 Mbps bitrate
SERVER_ADDR = ('127.0.0.1', 4662)
BUFFER_SIZE = 8192
START_UP = 5

## Full video
class Video:
        def __init__(self):
                self.uid = str(uuid.uuid4())
                self.size = int(random.gauss(AVG_TT_SIZE, .25 * AVG_TT_SIZE))
                self.chunks = []
                for c in range(0, self.size, CHUNK_SIZE):
                        self.chunks.append(c)


## Part of video that lives in node's cache
class Cached_Video_Chunk:
        def __init__(self, video_uid, chunk_id, data):
                self.video_uid = video_uid
                self.chunk_id = chunk_id
                self.data = data
                self.added = time.time()
                self.accessed = time.time()
                