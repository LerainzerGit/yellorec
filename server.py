#!/usr/bin/env python3
"""
Yellorec - Custom Rec Room Server
Support for Rec Room build 20260323
"""

import socket
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('yellorec')

# Server constants
SERVER_VERSION = "1.0.0"
RR_BUILD = "20260323"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080

class RRServer:
    """Custom Rec Room server implementation"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.clients = {}
        self.server_socket = None
        
    def start(self):
        """Start the Rec Room server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        logger.info(f"Yellorec server started on {self.host}:{self.port}")
        logger.info(f"Supporting Rec Room build: {RR_BUILD}")
        
        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"Client connected: {client_address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except KeyboardInterrupt:
                    break
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle individual client connection"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.clients[client_id] = {
            'socket': client_socket,
            'address': client_address,
            'connected_at': datetime.now(),
            'version': None
        }
        
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                message = data.decode('utf-8')
                response = self.process_message(message, client_id)
                
                if response:
                    client_socket.sendall(response.encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
            logger.info(f"Client disconnected: {client_id}")
    
    def process_message(self, message: str, client_id: str) -> str:
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'handshake':
                return self.handle_handshake(data, client_id)
            elif action == 'ping':
                return self.handle_ping(data)
            elif action == 'room_list':
                return self.handle_room_list(data)
            elif action == 'room_join':
                return self.handle_room_join(data, client_id)
            elif action == 'room_leave':
                return self.handle_room_leave(data, client_id)
            else:
                return json.dumps({'status': 'error', 'message': f'Unknown action: {action}'})
        
        except json.JSONDecodeError:
            return json.dumps({'status': 'error', 'message': 'Invalid JSON'})
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({'status': 'error', 'message': str(e)})
    
    def handle_handshake(self, data: Dict[str, Any], client_id: str) -> str:
        """Handle client handshake"""
        client_version = data.get('version')
        client_build = data.get('build')
        
        self.clients[client_id]['version'] = client_version
        
        logger.info(f"Handshake from {client_id} - Version: {client_version}, Build: {client_build}")
        
        response = {
            'status': 'ok',
            'server_version': SERVER_VERSION,
            'server_build': RR_BUILD,
            'timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(response)
    
    def handle_ping(self, data: Dict[str, Any]) -> str:
        """Handle ping message"""
        return json.dumps({
            'status': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    def handle_room_list(self, data: Dict[str, Any]) -> str:
        """Handle room list request"""
        rooms = [
            {
                'id': '1',
                'name': 'Rec Room',
                'players': 0,
                'max_players': 32
            },
            {
                'id': '2',
                'name': 'The Club',
                'players': 0,
                'max_players': 64
            }
        ]
        
        return json.dumps({
            'status': 'ok',
            'rooms': rooms
        })
    
    def handle_room_join(self, data: Dict[str, Any], client_id: str) -> str:
        """Handle room join request"""
        room_id = data.get('room_id')
        
        logger.info(f"Client {client_id} joining room {room_id}")
        
        return json.dumps({
            'status': 'ok',
            'room_id': room_id,
            'message': f'Joined room {room_id}'
        })
    
    def handle_room_leave(self, data: Dict[str, Any], client_id: str) -> str:
        """Handle room leave request"""
        room_id = data.get('room_id')
        
        logger.info(f"Client {client_id} leaving room {room_id}")
        
        return json.dumps({
            'status': 'ok',
            'message': f'Left room {room_id}'
        })
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Close all client connections
        for client_id, client_info in self.clients.items():
            try:
                client_info['socket'].close()
            except:
                pass
        
        if self.server_socket:
            self.server_socket.close()
        
        logger.info("Yellorec server stopped")

def main():
    """Main entry point"""
    server = RRServer(DEFAULT_HOST, DEFAULT_PORT)
    server.start()

if __name__ == '__main__':
    main()
