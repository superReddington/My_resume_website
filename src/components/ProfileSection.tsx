import type { Profile } from '../types/resume'
import { resolvePublicAsset } from '../utils/assetUrl'

interface ProfileSectionProps {
  profile: Profile
}

function getInitial(name: string) {
  return name.trim().charAt(0) || '?'
}

export function ProfileSection({ profile }: ProfileSectionProps) {
  const avatarSrc = profile.avatar ? resolvePublicAsset(profile.avatar) : undefined

  const metaItems = [
    { label: '邮箱', value: profile.email, href: `mailto:${profile.email}` },
    { label: '电话', value: profile.phone, href: `tel:${profile.phone}` },
    { label: '期望城市', value: profile.expectedCity },
    { label: '求职意向', value: profile.jobIntent },
    ...(profile.github
      ? [{ label: 'GitHub', value: profile.github, href: `https://github.com/${profile.github}` }]
      : []),
  ]

  return (
    <header className="hero">
      <div className="hero__content">
        <div className="hero__avatar">
          {avatarSrc ? (
            <img
              className="hero__avatar-image"
              src={avatarSrc}
              alt={`${profile.name}的头像`}
            />
          ) : (
            <span className="hero__avatar-fallback" aria-hidden="true">
              {getInitial(profile.name)}
            </span>
          )}
        </div>

        <div className="hero__main">
          <h1 className="hero__name">{profile.name}</h1>

          <dl className="hero__meta">
            {metaItems.map((item) => (
              <div key={item.label} className="hero__meta-item">
                <dt>{item.label}</dt>
                <dd>
                  {'href' in item && item.href ? (
                    <a href={item.href} target="_blank" rel="noreferrer">
                      {item.value}
                    </a>
                  ) : (
                    item.value
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </header>
  )
}
