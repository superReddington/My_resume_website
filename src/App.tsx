import resumeData from './data/resume.json'
import type { ResumeData } from './types/resume'
import { ProfileSection } from './components/ProfileSection'
import { SkillsSection } from './components/SkillsSection'
import { WorkExperienceSection } from './components/WorkExperienceSection'
import { ProjectsSection } from './components/ProjectsSection'
import { AdvantagesSection } from './components/AdvantagesSection'
import { EducationSection } from './components/EducationSection'

const resume = resumeData as ResumeData

function App() {
  return (
    <div className="page">
      <div className="page__glow page__glow--left" aria-hidden="true" />
      <div className="page__glow page__glow--right" aria-hidden="true" />

      <main className="main">
        <ProfileSection profile={resume.profile} />
        <SkillsSection skills={resume.skills} />
        <WorkExperienceSection experiences={resume.workExperience} />
        <ProjectsSection projects={resume.projects} />
        <AdvantagesSection advantages={resume.advantages} />
        <EducationSection education={resume.education} />
      </main>
    </div>
  )
}

export default App
