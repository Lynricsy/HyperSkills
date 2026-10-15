# INV-77: nightly invoice sync dies on the vendor's 503s

The vendor API answers 503 a few times a week, and a dropped connection now and then. Either one
kills the whole nightly sync.

## Acceptance

- A 503 or a network error is retried up to 3 times, waiting 200 ms, 400 ms and 800 ms.
- A 4xx is never retried.
- After the last retry fails, the job fails with the last error, as it does today.
