import { useEffect, useRef, useState, type FormEvent } from 'react'

const API_BASE = import.meta.env.VITE_ASSISTANT_API_URL ?? ''

const SUGGESTIONS = ['你目前在找什么工作？', '做过哪些 AI 项目？', '主要技术栈是什么？']

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

function getSessionId() {
  const key = 'resume-assistant-session'
  const existing = window.localStorage.getItem(key)
  if (existing) return existing
  const created = crypto.randomUUID()
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
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '你好，我是简历助手。可以问我工作经历、项目和技术栈。',
    },
  ])
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, open])

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
    <div className="chat-widget">
      {open ? (
        <section className="chat-panel" aria-label="简历助手">
          <header className="chat-panel__header">
            <div>
              <strong>简历助手</strong>
              <p>基于已上传的简历 PDF 回答</p>
            </div>
            <button type="button" className="chat-panel__close" onClick={() => setOpen(false)}>
              关闭
            </button>
          </header>
          <div className="chat-panel__messages" ref={listRef}>
            {messages.map((item, index) => (
              <div key={`${item.role}-${index}`} className={`chat-bubble chat-bubble--${item.role}`}>
                {item.content || (busy && item.role === 'assistant' ? '正在检索简历…' : '')}
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
              placeholder="问问经历或项目…"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()}>
              发送
            </button>
          </form>
        </section>
      ) : null}
      <button type="button" className="chat-fab" onClick={() => setOpen((value) => !value)}>
        {open ? '收起' : '问我'}
      </button>
    </div>
  )
}
