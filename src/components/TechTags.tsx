interface TechTagsProps {
  tags: string[]
}

export function TechTags({ tags }: TechTagsProps) {
  if (tags.length === 0) return null

  return (
    <div className="tech-tags">
      {tags.map((tag) => (
        <span key={tag} className="tech-tag">
          {tag}
        </span>
      ))}
    </div>
  )
}
