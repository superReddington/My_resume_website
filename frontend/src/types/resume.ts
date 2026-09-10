export interface Period {
  start: string
  end: string
}

export interface Profile {
  name: string
  age: number
  phone: string
  email: string
  jobIntent: string
  expectedCity: string
  summary?: string
  github?: string
  avatar?: string
}

export interface SkillGroup {
  category: string
  items?: string[]
  description?: string
}

export interface WorkExperience {
  company: string
  position: string
  period: Period
  description?: string
  content: string[]
  techStack?: string[]
}

export interface ProjectExperience {
  name: string
  role: string
  content: string[]
  techStack: string[]
}

export interface Education {
  school: string
  degree: string
  major: string
  period: Period
}

export interface ResumeData {
  profile: Profile
  skills: SkillGroup[]
  workExperience: WorkExperience[]
  projects: ProjectExperience[]
  advantages: string[]
  education: Education[]
}
