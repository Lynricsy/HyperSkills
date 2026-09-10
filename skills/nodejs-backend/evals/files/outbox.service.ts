import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common'
import { Pool } from 'pg'

@Injectable()
export class OutboxService implements OnModuleInit, OnModuleDestroy {
  private pool!: Pool
  private timer!: NodeJS.Timeout

  onModuleInit(): void {
    this.pool = new Pool({ connectionString: process.env.DATABASE_URL })
    this.pool.connect()
    this.timer = setInterval(() => this.flush(), 1000)
  }

  async onModuleDestroy(): Promise<void> {
    clearInterval(this.timer)
    await this.pool.end()
  }

  private async flush(): Promise<void> {
    const { rows } = await this.pool.query(
      'select id, payload from outbox where sent_at is null limit 100',
    )
    for (const row of rows) {
      await fetch('https://events.internal/publish', {
        method: 'POST',
        body: JSON.stringify(row.payload),
      })
      await this.pool.query('update outbox set sent_at = now() where id = $1', [
        row.id,
      ])
    }
  }
}
