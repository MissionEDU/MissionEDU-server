import socket
import sys
import os

#class used to start, connect and manage the rsal
class ARS():
    server_address = 'uds_socket'
    connection = None 
    sock = None 

    #initializes rs object, creates uds socket used for connection
    def __init__(self):
        # Make sure the socket does not already exist
        try:
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise

        # Create a UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Bind the socket to the port
        self.sock.bind(self.server_address)

        # Listen for incoming connections
        self.sock.listen(1)

    #handles input from ars
    def receive(self):
        finished = False

        counter = 0
        msg = self.connection.recv(2048).decode("utf-8")
        msg = msg.strip(' ')
        if not msg:
            return False
       
        return msg.encode("utf-8")

    #handles output to ars
    def send(self, msg):
        msg = msg.ljust(2048)
        self.connection.sendall(msg.encode())

    #launches and connects ars
    def connect(self):
        # Wait for a connection
        self.connection, client_address = self.sock.accept()
