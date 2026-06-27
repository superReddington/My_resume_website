import { Section } from './Section'
import type { SkillGroup } from '../types/resume'

interface SkillsSectionProps {
  skills: SkillGroup[]
}

export function SkillsSection({ skills }: SkillsSectionProps) {
  return (
    <Section id="skills" title="专业技能">
      <ul className="skill-list">
        {skills.map((group) => (
          <li key={group.category} className="skill-list__item">
            <strong className="skill-list__category">{group.category}</strong>
            {group.description ? (
              <p className="skill-list__text">{group.description}</p>
            ) : (
              <p className="skill-list__text">{group.items?.join('、')}</p>
            )}
          </li>
        ))}
      </ul>
    </Section>
  )
}
