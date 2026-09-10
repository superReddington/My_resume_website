import type { ReactNode } from 'react'

interface SectionProps {
  id: string
  title: string
  children: ReactNode
}

export function Section({ id, title, children }: SectionProps) {
  return (
    <section id={id} className="section">
      <h2 className="section__title">
        <span className="section__marker" aria-hidden="true" />
        {title}
      </h2>
      <div className="section__body">{children}</div>
    </section>
  )
}
