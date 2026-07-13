import { Link } from "react-router-dom"

export function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
      <h1 className="text-2xl font-semibold text-stone-900">로그인</h1>
      <p className="text-sm text-stone-600">인증 플로우는 다음 단계에서 연결합니다.</p>
      <Link className="text-sm text-stone-900 underline underline-offset-4" to="/">
        홈으로
      </Link>
    </main>
  )
}
