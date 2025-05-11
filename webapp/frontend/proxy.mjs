//proxy to redirect requests to either frontend or backend server
//any requests to /api will be redirected to the backend server, removing the /api prefix
//all other requests go to the frontend server. The frontend server is assumed to be running on port 3000 and the backend server on port 8000

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

const app = express();
const PORT = process.env.PORT || 5000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';

// Request logging middleware
app.use((req, res, next) => {
  const destination = req.url.startsWith('/api') ? 'backend' : 'frontend';
  const target = req.url.startsWith('/api') ? BACKEND_URL : FRONTEND_URL;
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} -> ${destination} (${target})`);
  next();
});

// Proxy middleware to redirect requests to the backend server
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '',
  },
}));

// Proxy middleware to redirect all other requests to the frontend server
app.use('/', createProxyMiddleware({
  target: FRONTEND_URL,
  changeOrigin: true,
  ws: true, // Enable WebSocket proxying
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).send('Proxy error');
  }
}));

// Start the server
app.listen(PORT, () => {
  console.log(`Proxy server is running on http://localhost:${PORT}`);
});
