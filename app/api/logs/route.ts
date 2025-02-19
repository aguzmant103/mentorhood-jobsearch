import { WebSocketServer, WebSocket } from 'ws';
import { createServer } from 'http';
import { NextResponse } from 'next/server';

// Declare global types
declare global {
  // eslint-disable-next-line no-var
  var wss: WebSocketServer;
  // eslint-disable-next-line no-var
  var clients: Set<WebSocket>;
}

const wss = new WebSocketServer({ noServer: true });
const clients = new Set<WebSocket>();

if (!global.wss) {
  global.wss = wss;
  global.clients = clients;
}

export function GET() {
  const upgrade = process.env.NODE_ENV === 'development' 
    ? { 'message': 'Development mode - WebSocket available at ws://localhost:3001' }
    : { 'message': 'WebSocket upgrade required' };
    
  return NextResponse.json(upgrade);
}

// Create WebSocket server on port 3001 for development
if (process.env.NODE_ENV === 'development') {
  const server = createServer();
  server.listen(3001);
  
  server.on('upgrade', (request, socket, head) => {
    wss.handleUpgrade(request, socket, head, (ws: WebSocket) => {
      global.clients.add(ws);
      ws.on('close', () => global.clients.delete(ws));
    });
  });
}

export async function POST(request: Request) {
  const log = await request.json();
  
  // Broadcast to all WebSocket clients
  global.clients?.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(log));
    }
  });
  
  return NextResponse.json({ success: true });
} 