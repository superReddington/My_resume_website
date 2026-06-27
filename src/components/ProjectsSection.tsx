import { Section } from './Section'
import { ExpandableCard } from './ExpandableCard'
import { TechTags } from './TechTags'
import type { ProjectExperience } from '../types/resume'

interface ProjectsSectionProps {
  projects: ProjectExperience[]
}

export function ProjectsSection({ projects }: ProjectsSectionProps) {
  return (
    <Section id="projects" title="项目经历">
      <div className="card-stack">
        {projects.map((project, index) => (
          <ExpandableCard
            key={project.name}
            title={project.name}
            subtitle={project.role}
            defaultOpen={index === 0}
            footer={<TechTags tags={project.techStack} />}
          >
            <ul className="content-list">
              {project.content.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </ExpandableCard>
        ))}
      </div>
    </Section>
  )
}
