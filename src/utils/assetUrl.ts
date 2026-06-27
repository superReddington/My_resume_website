/** 解析 public 目录下的静态资源路径，兼容部署子路径 */
export function resolvePublicAsset(path: string) {
  const normalized = path.replace(/^\//, '')
  return `${import.meta.env.BASE_URL}${normalized}`
}
