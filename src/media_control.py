import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import zmq
from src.config import Config

config = Config()
port = config.configparser.get('Network', 'port')

context = zmq.Context()
socket = context.socket(zmq.REQ)

if port == 0:
    with open('address.txt') as f:
        address = f.readline()
    address = address.replace('*', 'localhost')
else:
    address = 'tcp://localhost:%s' % port

socket.connect(address)
socket.send_string('NEXT')
socket.recv_string()
time.sleep(4)
socket.disconnect(address)
sys.exit()
