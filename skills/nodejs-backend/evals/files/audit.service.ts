import { Injectable, Logger } from '@nestjs/common'

@Injectable()
export class AuditService {
  private readonly logger = new Logger(AuditService.name)
  private currentUserId: string | null = null
  private currentRequestId: string | null = null

  bindRequest(userId: string, requestId: string): void {
    this.currentUserId = userId
    this.currentRequestId = requestId
  }

  record(action: string, subject: string): void {
    this.logger.log(
      `requestId=${this.currentRequestId} user=${this.currentUserId} action=${action} subject=${subject}`,
    )
  }
}
