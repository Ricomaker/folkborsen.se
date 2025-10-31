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
    // If the file isn't available on the function filesystem (common on serverless
    // platforms), try fetching the static file from the deployed site's static
    // assets using the request Host header. This lets the API return the committed
    // `folkborsen_feed.xml` when it's deployed as a static file rather than bundled
    // with the function.
    try {
      const proto = (req.headers['x-forwarded-proto'] || 'https').split(',')[0].trim();
      const host = req.headers.host || 'www.folkborsen.se';
      const url = `${proto}://${host}/folkborsen_feed.xml`;
      const client = url.startsWith('https') ? require('https') : require('http');
      return client.get(url, (r) => {
        let data = '';
        r.setEncoding('utf8');
        r.on('data', chunk => data += chunk);
        r.on('end', () => {
          // forward headers
          res.setHeader('Content-Type', 'application/rss+xml; charset=utf-8');
          res.setHeader('Access-Control-Allow-Origin', '*');
          return res.end(data);
        });
      }).on('error', () => {
        const fallback = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Folkbörsen Feed (fallback)</title><link>https://folkborsen.se</link><description>Fallback feed</description></channel></rss>';
        res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8' });
        return res.end(fallback);
      });
    } catch (e) {
      const fallback = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Folkbörsen Feed (fallback)</title><link>https://folkborsen.se</link><description>Fallback feed</description></channel></rss>';
      res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8' });
      return res.end(fallback);
    }
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
