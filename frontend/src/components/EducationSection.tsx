import { Section } from './Section'
import type { Education } from '../types/resume'

interface EducationSectionProps {
  education: Education[]
}

function formatPeriod(start: string, end: string) {
  return `${start} — ${end}`
}

export function EducationSection({ education }: EducationSectionProps) {
  return (
    <Section id="education" title="教育经历">
      <div className="education-list">
        {education.map((item) => (
          <article
            key={`${item.school}-${item.period.start}`}
            className="education-item"
          >
            <div className="education-header">
              <div>
                <h3 className="education-school">{item.school}</h3>
                <p className="education-major">
                  {item.degree} · {item.major}
                </p>
              </div>
              <time className="education-period">
                {formatPeriod(item.period.start, item.period.end)}
              </time>
            </div>
          </article>
        ))}
      </div>
    </Section>
  )
}
