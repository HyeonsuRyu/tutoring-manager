import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { getHealth } from "@/features/health/api/health"

export function HomePage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  })

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-16">
      <div>
        <p className="text-sm tracking-wide text-stone-500">Tutoring Manager</p>
        <h1 className="mt-2 text-3xl font-semibold text-stone-900">과외 관리</h1>
        <p className="mt-3 max-w-xl text-stone-600">
          교사 중심의 학원 과외 플랫폼 스캐폴드입니다. 학생·일정·진도는 이후 기능에서
          이어집니다.
        </p>
      </div>

      <div className="flex gap-4 text-sm">
        <Link className="text-stone-900 underline underline-offset-4" to="/login">
          로그인
        </Link>
      </div>

      <section className="rounded-lg border border-stone-200 bg-white p-4 text-sm text-stone-700">
        <p className="font-medium text-stone-900">API 상태</p>
        {health.isLoading && <p className="mt-2">확인 중…</p>}
        {health.isError && <p className="mt-2 text-red-700">백엔드에 연결할 수 없습니다.</p>}
        {health.data && (
          <p className="mt-2">
            {health.data.app}: {health.data.status}
          </p>
        )}
      </section>
    </main>
  )
}
