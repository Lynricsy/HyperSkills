import http from 'node:http';

// Never expose the dev API to the network: listen on loopback only.
const HOST = process.env.HOST ?? '127.0.0.1';
const PORT = Number(process.env.PORT ?? 3000);

http
  .createServer((req, res) => {
    if (req.url === '/health') return res.end('ok');
    res.statusCode = 404;
    res.end();
  })
  .listen(PORT, HOST, () => console.log(`listening on ${HOST}:${PORT}`));
