# Android (Kotlin + Compose)

[docs/mobile-android.md](../docs/mobile-android.md) 기준 MVP입니다.

## 빌드

Android Studio에서 `android/` 폴더를 열고 Gradle Sync 후 실행합니다.

- 에뮬레이터 API: `http://10.0.2.2:8000/api/v1/`
- 로컬 서버: `uv run python manage.py runserver 0.0.0.0:8000`

## 포함 화면

- 로그인 (JWT)
- 학생 목록
- 주간 수업 현황
- (추후) 달력·완료·소셜
