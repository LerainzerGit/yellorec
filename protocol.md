# Yellorec Protocol Documentation

## Overview
Yellorec is a custom Rec Room server implementation supporting build 20260323. This document outlines the communication protocol between clients and the server.

## Build Information
- **Build Number**: 20260323
- **Protocol Version**: 1.0
- **Server Version**: 1.0.0

## Message Format
All messages are JSON-encoded strings sent over TCP sockets.

### Base Message Structure
```json
{
  "action": "action_name",
  "data": {}
}
```

## Supported Actions

### 1. Handshake
Client initiates connection with server information.

**Request**:
```json
{
  "action": "handshake",
  "version": "client_version",
  "build": "20260323",
  "username": "player_name"
}
```

**Response**:
```json
{
  "status": "ok",
  "server_version": "1.0.0",
  "server_build": "20260323",
  "timestamp": "2026-09-09T00:00:00"
}
```

### 2. Ping
Keep-alive message.

**Request**:
```json
{
  "action": "ping"
}
```

**Response**:
```json
{
  "status": "pong",
  "timestamp": "2026-09-09T00:00:00"
}
```

### 3. Room List
Request available rooms.

**Request**:
```json
{
  "action": "room_list"
}
```

**Response**:
```json
{
  "status": "ok",
  "rooms": [
    {
      "id": "1",
      "name": "Rec Room",
      "players": 0,
      "max_players": 32
    }
  ]
}
```

### 4. Room Join
Join a specific room.

**Request**:
```json
{
  "action": "room_join",
  "room_id": "1"
}
```

**Response**:
```json
{
  "status": "ok",
  "room_id": "1",
  "message": "Joined room 1"
}
```

### 5. Room Leave
Leave current room.

**Request**:
```json
{
  "action": "room_leave",
  "room_id": "1"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Left room 1"
}
```

## Status Codes
- `ok` - Request successful
- `error` - Request failed
- `unauthorized` - Authentication required
- `not_found` - Resource not found

## Error Handling
All error responses follow this format:
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Connection Management
- Default port: 8080
- Connection timeout: 300 seconds
- Max simultaneous connections: 1000
- Keep-alive interval: 30 seconds

## Authentication
Future implementation for user authentication and verification.

## Security Notes
- All messages should be validated before processing
- Input sanitization is required for user-provided data
- Consider implementing TLS/SSL for encrypted connections in production
