// chat-gateway: Express app currently deployed on Lambda (nodejs20.x, x86_64) behind API Gateway REST.
const express = require('express');
const serverlessExpress = require('@codegenie/serverless-express');
const sharp = require('sharp');
const { streamCompletion } = require('./llm');

const app = express();
app.use(express.json({ limit: '2mb' }));

// Set by the auth middleware, read by the handlers below.
let currentUser = null;

app.use(async (req, res, next) => {
  currentUser = await verifySession(req.headers.authorization);
  next();
});

app.post('/chat', async (req, res) => {
  // Today this buffers the whole completion; product wants token-by-token SSE.
  let text = '';
  for await (const token of streamCompletion(req.body.messages, { user: currentUser.id })) {
    text += token;
  }
  res.json({ text, user: currentUser.id });
});

app.post('/avatar', async (req, res) => {
  const png = await sharp(Buffer.from(req.body.image, 'base64')).resize(256).png().toBuffer();
  res.type('png').send(png);
});

async function verifySession(header) {
  // calls the identity service; ~40 ms
  return { id: header ? header.slice(-8) : 'anonymous' };
}

exports.handler = serverlessExpress({ app });
