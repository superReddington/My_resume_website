import { Section } from './Section'
import { ExpandableCard } from './ExpandableCard'
import { TechTags } from './TechTags'
import type { WorkExperience } from '../types/resume'

interface WorkExperienceSectionProps {
  experiences: WorkExperience[]
}

function formatPeriod(start: string, end: string) {
  return `${start} — ${end}`
}

export function WorkExperienceSection({ experiences }: WorkExperienceSectionProps) {
  return (
    <Section id="work" title="工作经历">
      <div className="card-stack">
        {experiences.map((item, index) => (
          <ExpandableCard
            key={`${item.company}-${item.period.start}`}
            title={
              <>
                <span className="exp-card__company">{item.company}</span>
                <span className="exp-card__divider"> · </span>
                <span className="exp-card__role">{item.position}</span>
              </>
            }
            period={formatPeriod(item.period.start, item.period.end)}
            description={item.description}
            defaultOpen={index === 0}
            footer={item.techStack ? <TechTags tags={item.techStack} /> : undefined}
          >
            <ul className="content-list">
              {item.content.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </ExpandableCard>
        ))}
      </div>
    </Section>
  )
}
