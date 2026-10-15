// services/chat (NestJS 12, socket.io)
import { Injectable, Scope } from '@nestjs/common'
import {
  ConnectedSocket,
  MessageBody,
  SubscribeMessage,
  WebSocketGateway,
} from '@nestjs/websockets'
import { Socket } from 'socket.io'

// Request-scoped, so every incoming message gets a fresh buffer.
@Injectable({ scope: Scope.REQUEST })
export class MentionBuffer {
  readonly mentions: string[] = []

  collect(text: string) {
    for (const match of text.matchAll(/@(\w+)/g)) {
      this.mentions.push(match[1])
    }
  }
}

@WebSocketGateway({ namespace: '/rooms' })
export class PresenceGateway {
  constructor(private readonly buffer: MentionBuffer) {}

  @SubscribeMessage('message')
  handleMessage(@MessageBody() body: { room: string; text: string }, @ConnectedSocket() socket: Socket) {
    this.buffer.collect(body.text)
    socket.to(body.room).emit('message', { text: body.text, mentions: this.buffer.mentions })
  }
}
