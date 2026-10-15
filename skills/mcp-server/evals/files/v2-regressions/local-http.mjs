// Local HTTP entry point used by the dashboard widget in our Electron app.
// The widget is a sandboxed <iframe sandbox="allow-scripts"> loaded from file://.../widget.html
// and calls fetch("http://127.0.0.1:8931/mcp") directly.
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { buildServer } from "./server.mjs";

const app = createMcpExpressApp({
  host: "127.0.0.1",
  // Added after the v2 upgrade started returning 403 to the widget. Did not help.
  allowedOrigins: ["null", "file://", "http://localhost:5173"],
});

app.post("/mcp", async (req, res) => {
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => transport.close());
  await buildServer().connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(8931, "127.0.0.1");
