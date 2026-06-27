import { Section } from './Section'

interface AdvantagesSectionProps {
  advantages: string[]
}

export function AdvantagesSection({ advantages }: AdvantagesSectionProps) {
  return (
    <Section id="advantages" title="个人优势">
      <ul className="advantage-list">
        {advantages.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </Section>
  )
}
