import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'

import pigHead from '../assets/zhuzhu-pig.png'

const API_BASE = import.meta.env.VITE_ASSISTANT_API_URL ?? ''

const SUGGESTIONS = ['你目前在找什么工作？', '做过哪些 AI 项目？', '主要技术栈是什么？']

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

function renderInlineMarkdown(text: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const pattern = /\*\*(.+?)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let key = 0

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index))
    }
    nodes.push(<strong key={`b-${key++}`}>{match[1]}</strong>)
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex))
  }

  return nodes
}

function createSessionId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getSessionId() {
  const key = 'resume-assistant-session'
  const existing = window.localStorage.getItem(key)
  if (existing) return existing
  const created = createSessionId()
  window.localStorage.setItem(key, created)
  return created
}

async function readSse(
  response: Response,
  onToken: (text: string) => void,
) {
  if (!response.body) {
    throw new Error('浏览器不支持流式读取')
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventName = 'message'

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      for (const line of part.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const data = JSON.parse(line.slice(5).trim()) as {
            content?: string
            message?: string
          }
          if (eventName === 'token' && data.content) {
            onToken(data.content)
          }
          if (eventName === 'error') {
            throw new Error(data.message || '回答失败')
          }
          eventName = 'message'
        }
      }
    }
  }
}

export function ChatWidget() {
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '嗨，我是猪猪小敏。朱植敏的经历、项目和技术栈我都装在脑子里了，想挖就尽管问～',
    },
  ])
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages])

  async function send(text: string) {
    const question = text.trim()
    if (!question || busy) return
    setInput('')
    setBusy(true)
    setMessages((current) => [
      ...current,
      { role: 'user', content: question },
      { role: 'assistant', content: '' },
    ])

    try {
      const response = await fetch(`${API_BASE}/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: getSessionId(),
          message: question,
        }),
      })
      if (!response.ok) {
        throw new Error('助手暂时不可用，请稍后再试')
      }
      await readSse(response, (token) => {
        setMessages((current) => {
          const next = [...current]
          const last = next[next.length - 1]
          if (last?.role === 'assistant') {
            next[next.length - 1] = { ...last, content: last.content + token }
          }
          return next
        })
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : '回答失败'
      setMessages((current) => {
        const next = [...current]
        next[next.length - 1] = { role: 'assistant', content: message }
        return next
      })
    } finally {
      setBusy(false)
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void send(input)
  }

  return (
    <aside className="chat-widget">
      <section className="chat-panel" aria-label="猪猪小敏">
        <header className="chat-panel__header">
          <img
            className={`chat-panel__mascot${busy ? ' chat-panel__mascot--busy' : ''}`}
            src={pigHead}
            alt=""
            width={40}
            height={40}
          />
          <strong>猪猪小敏</strong>
        </header>
        <div className="chat-panel__messages" ref={listRef}>
          {messages.map((item, index) => (
            <div key={`${item.role}-${index}`} className={`chat-bubble chat-bubble--${item.role}`}>
              {item.content
                ? renderInlineMarkdown(item.content)
                : busy && item.role === 'assistant'
                  ? '猪猪小敏想想…'
                  : ''}
            </div>
          ))}
        </div>
        <div className="chat-panel__suggestions">
          {SUGGESTIONS.map((item) => (
            <button key={item} type="button" disabled={busy} onClick={() => void send(item)}>
              {item}
            </button>
          ))}
        </div>
        <form className="chat-panel__form" onSubmit={onSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="问问猪猪小敏…"
            disabled={busy}
          />
          <button type="submit" disabled={busy || !input.trim()}>
            发送
          </button>
        </form>
      </section>
    </aside>
  )
}
