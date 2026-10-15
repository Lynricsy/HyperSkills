import { describe, expect, it } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { McpError } from "@modelcontextprotocol/sdk/types.js";
import { buildServer } from "../src/server.js";

async function connect() {
  const [a, b] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test", version: "0" });
  await Promise.all([buildServer().connect(a), client.connect(b)]);
  return client;
}

describe("tickets server", () => {
  it("advertises the golden capabilities", async () => {
    const client = await connect();
    expect(client.getServerCapabilities()).toEqual({
      tools: { listChanged: true },
      resources: {},
      prompts: {},
    });
  });

  it("has no prompts yet", async () => {
    const client = await connect();
    await expect(client.listPrompts()).rejects.toThrow(/MCP error -32601/);
  });

  it("reports an unknown tool as a tool error", async () => {
    const client = await connect();
    const result = await client.callTool({ name: "close_ticket", arguments: {} });
    expect(result.isError).toBe(true);
  });

  it("maps protocol errors", async () => {
    const client = await connect();
    try {
      await client.readResource({ uri: "audit://nobody/1999-01-01" });
    } catch (e) {
      expect(e).toBeInstanceOf(McpError);
    }
  });
});
