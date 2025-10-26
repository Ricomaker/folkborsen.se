const fs = require('fs');
const path = require('path');
const http = require('http');

function respondWithFeed(req, res) {
  const feedPath = path.resolve(process.cwd(), 'folkborsen_feed.xml');

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  try {
    const feed = fs.readFileSync(feedPath, 'utf8');
    res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8' });
    return res.end(feed);
  } catch (err) {
    const fallback = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Folkbörsen Feed (fallback)</title><link>https://folkborsen.se</link><description>Fallback feed</description></channel></rss>';
    res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8' });
    return res.end(fallback);
  }
}

// Export handler for serverless platforms that use (req, res)
module.exports = (req, res) => {
  // If the platform provides res.status / res.send (like Next/Vercel), they still accept writeHead/end.
  respondWithFeed(req, res);
};

// If run directly, start a tiny HTTP server for local testing
if (require.main === module) {
  const port = process.env.PORT || 3000;
  const server = http.createServer((req, res) => {
    if (req.url === '/api/generate-feed' || req.url === '/api/generate_feed' || req.url === '/generate-feed' ) {
      return respondWithFeed(req, res);
    }
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  });

  server.listen(port, () => {
    console.log(`Local feed server listening: http://localhost:${port}/api/generate-feed`);
  });
}
