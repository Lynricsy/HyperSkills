// src/rooms.ts
import { DurableObject } from "cloudflare:workers";

export class GameRoom extends DurableObject<Env> {
  async join(playerId: string): Promise<number> {
    const players = (await this.ctx.storage.get<string[]>("players")) ?? [];
    players.push(playerId);
    await this.ctx.storage.put("players", players);
    await this.ctx.storage.setAlarm(Date.now() + 30_000);
    return players.length;
  }

  async settle(): Promise<void> {
    const players = (await this.ctx.storage.get<string[]>("players")) ?? [];
    for (const p of players) {
      await this.env.LEDGER.send({ player: p, room: this.ctx.id.toString() });
    }
    await this.ctx.storage.setAlarm(Date.now() + 30_000);
  }

  async alarm(): Promise<void> {
    await this.settle();
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const room = new URL(request.url).searchParams.get("room") ?? "lobby";
    const count = await env.ROOM.getByName(room).join(crypto.randomUUID());
    return Response.json({ count });
  },
} satisfies ExportedHandler<Env>;
