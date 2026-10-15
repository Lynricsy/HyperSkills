"use client"

import { useState } from "react"
import type { UIMessage } from "ai"
import { IconChevronDown, IconTool } from "@tabler/icons-react"

import { Bubble, BubbleContent } from "@workspace/ui/components/bubble"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible"
import { Marker } from "@workspace/ui/components/marker"
import { Message } from "@workspace/ui/components/message"

// One assistant turn from useChat(): reasoning, tool calls and the text answer.
export function AssistantTurn({
  message,
  isStreaming,
}: {
  message: UIMessage
  isStreaming: boolean
}) {
  const [open, setOpen] = useState(true)

  return (
    <Message>
      {message.parts.map((part, index) => {
        if (part.type === "reasoning") {
          return (
            <Collapsible key={index} open={open} onOpenChange={setOpen}>
              <CollapsibleTrigger className="flex items-center gap-1 text-sm text-muted-foreground">
                {isStreaming ? "Thinking..." : "Thought for a few seconds"}
                <IconChevronDown className="size-4" />
              </CollapsibleTrigger>
              <CollapsibleContent className="opacity-70">
                {part.text}
              </CollapsibleContent>
            </Collapsible>
          )
        }

        if (part.type.startsWith("tool-")) {
          const tool = part as {
            type: string
            state: string
            output?: unknown
          }
          return (
            <div key={index}>
              <Marker>
                <IconTool className="size-3" />
                {tool.state === "output-available" ? "Ran" : "Running"}{" "}
                {tool.type.slice(5)}
              </Marker>
              {tool.output !== undefined && (
                <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-muted p-3 font-mono text-xs whitespace-pre-wrap">
                  {JSON.stringify(tool.output, null, 2)}
                </pre>
              )}
            </div>
          )
        }

        if (part.type === "text") {
          return (
            <Bubble key={index}>
              <BubbleContent>{part.text}</BubbleContent>
            </Bubble>
          )
        }

        return null
      })}
    </Message>
  )
}
