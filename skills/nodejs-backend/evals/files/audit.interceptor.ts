import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common'
import { Observable } from 'rxjs'
import { AuditService } from './audit.service'

@Injectable()
export class AuditInterceptor implements NestInterceptor {
  constructor(private readonly audit: AuditService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const request = context.switchToHttp().getRequest()
    this.audit.bindRequest(
      request.user?.id ?? 'anonymous',
      String(request.headers['x-request-id'] ?? ''),
    )
    return next.handle()
  }
}
