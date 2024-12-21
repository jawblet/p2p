from app import Node
from server import Server
from threading import Thread
from multiprocessing import Process
import time

def server(log, bw):
  s = Server(log, .1, bw, 10)

def peer(log, i, nv, type, policy,):
  n = Node(log, .1 , 50000, type, 1, policy)
  for _ in range(0, nv):
    n.get_random_video()
    
def test_no_p2p(np, nv, bw):
  server_thread = Process(target=server, daemon=True, args=(f'server_no_p2p_{bw}.txt', bw,))
  server_thread.start()
  
  time.sleep(1)
  
  nodes = []
  for i in range(0, np):
  
    nodes.append(Thread(target=peer, daemon=True, args=(f'node_no_p2p_{bw}.txt', i+1, nv, 'CS',)))
    nodes[-1].start()

  for node in nodes:
      node.join()
  
  server_thread.terminate()
      
def test_p2p(np, nv, bw):
  server_thread = Process(target=server, daemon=True, args=(f'server_p2p_{bw}.txt', bw,))
  server_thread.start()
  
  time.sleep(1)
  
  nodes = []
  for i in range(0, np):
  
    nodes.append(Thread(target=peer, daemon=True, args=(f'node_p2p_{bw}.txt', i+1, nv, 'P2P', )))
    nodes[-1].start()

  for node in nodes:
      node.join() 
      
  server_thread.terminate()
  
def test_lra(np, nv, bw):
  server_thread = Process(target=server, daemon=True, args=(f'server_lra.txt', bw,))
  server_thread.start()
  
  time.sleep(1)
  
  nodes = []
  for i in range(0, np):
  
    nodes.append(Process(target=peer, daemon=True, args=(f'node_lra.txt', i+1, nv, 'P2P', 'lra',)))
    nodes[-1].start()

  for node in nodes:
      node.join(timeout=30) 
      
  for node in nodes:
    if node.is_alive():
      node.terminate()
  
  server_thread.terminate()
      
def test_lru(np, nv, bw, sys):
  server_thread = Process(target=server, daemon=True, args=(f'server_lru_{sys}.txt', bw,))
  server_thread.start()
  
  time.sleep(1)
  
  nodes = []
  for i in range(0, np):
    nodes.append(Process(target=peer, daemon=True, args=(f'node_lru_{sys}.txt', i+1, nv, sys, 'lru',)))
    nodes[-1].start()

  for node in nodes:
    node.join(timeout=30) 
      
  for node in nodes:
    if node.is_alive():
      node.terminate()
      
  server_thread.terminate()

if __name__ == "__main__":
  np = 10
  nv = 10
  
  bw = 1000000
  
  test_lru(np, nv, bw, 'CS')
  test_lru(np, nv, bw, 'P2P')
  


    
    
