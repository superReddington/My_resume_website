import { useId, useState, type ReactNode } from 'react'

interface ExpandableCardProps {
  title: ReactNode
  subtitle?: ReactNode
  period?: string
  description?: string
  defaultOpen?: boolean
  children: ReactNode
  footer?: ReactNode
}

export function ExpandableCard({
  title,
  subtitle,
  period,
  description,
  defaultOpen = false,
  children,
  footer,
}: ExpandableCardProps) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = useId()

  return (
    <article className={`exp-card${open ? ' exp-card--open' : ''}`}>
      <button
        type="button"
        className="exp-card__trigger"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <div className="exp-card__heading">
          <div className="exp-card__titles">
            <h3 className="exp-card__title">{title}</h3>
            {subtitle && <p className="exp-card__subtitle">{subtitle}</p>}
          </div>
          {period && <time className="exp-card__period">{period}</time>}
        </div>
        <span className="exp-card__chevron" aria-hidden="true" />
      </button>

      <div id={panelId} className="exp-card__panel" hidden={!open}>
        {description && <p className="exp-card__description">{description}</p>}
        <div className="exp-card__body">{children}</div>
        {footer && <div className="exp-card__footer">{footer}</div>}
      </div>
    </article>
  )
}
