import { DurableObject } from "cloudflare:workers";

export class ProjectDO extends DurableObject<Env> {
  async listTasks(status: string) {
    const start = Date.now();
    const rows = this.ctx.storage.sql
      .exec("SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC", status)
      .toArray();
    console.log({ message: "listTasks", status, ms: Date.now() - start, count: rows.length });
    return rows;
  }
}
