# chat-gateway notes

- Region: us-east-1. Callers: our web app (browsers, public) and the internal `billing-worker` service.
- Traffic: spiky, 0-300 concurrent chats. A chat request waits 20-90 s on the LLM provider and
  spends almost no CPU while waiting.
- Today: API Gateway REST API -> Lambda (`handler` above), 29 s integration timeout, so long chats fail.
- Secrets: `LLM_API_KEY` is set as a plain Lambda environment variable in the SAM template.
- Build: GitHub Actions `ubuntu-latest` (x86_64) runs `npm ci && zip -r function.zip .`.
- Ask from product: stream tokens to the browser over SSE, keep it on Lambda, lowest cost.
