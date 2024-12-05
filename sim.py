from app import Node
from server import Server
from threading import Thread

def server():
  s = Server('server_log.txt', .5, 50000)

def node(i):
  n = Node(f'node-{i}.txt', .1 * i, 10000 * i)
  for _ in range(0,4):
    n.get_random_video()

if __name__ == "__main__":
  server_thread = Thread(target=server, daemon=True, args=())
  server_thread.start()
  
  nodes = []
  for i in range(0, 10):
  
    nodes.append(Thread(target=node, daemon=True, args=(i+1,)))
    nodes[-1].start()

  for node in nodes:
      node.join()
    
    
