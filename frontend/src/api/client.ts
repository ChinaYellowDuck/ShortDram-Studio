import axios from 'axios'

/** 统一的 axios 实例，开发环境经 Vite 代理转发到后端 */
export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

/** 将 axios / FastAPI 错误转换为可读消息 */
export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((d: { msg?: string; loc?: (string | number)[] }) =>
          d.loc ? `${d.loc.join('.')}: ${d.msg ?? ''}` : d.msg ?? '',
        )
        .join('; ')
    }
    if (err.code === 'ERR_NETWORK') return '无法连接后端服务，请确认后端已启动（8000 端口）'
    return err.message
  }
  return String(err)
}
