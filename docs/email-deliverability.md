# 이메일 도달률·스팸 방지 (배포 시 점검)

인증·비밀번호 재설정 메일이 **수신함에 도착**하도록 하기 위한 체크리스트입니다.  
**서비스를 공개 도메인으로 배포할 때** 이 문서를 따라 설정합니다. 개발(`DOMAIN=local`) 단계에서는 생략 가능합니다.

**발송**: [Resend](https://resend.com) — 앱 설정은 [auth.md](./auth.md)

---

## 1. 사전 조건

- [ ] 프로덕션 `DOMAIN` 확정 (예: `tutor.example.com`)
- [ ] Resend 계정 생성, **Sending Domain** 추가
- [ ] `DEFAULT_FROM_EMAIL` = 해당 도메인 (예: `noreply@tutor.example.com`)

---

## 2. DNS 레코드 (Resend 대시보드 안내 따름)

도메인 DNS에 Resend가 제시하는 값을 추가한다.

| 종류 | 목적 |
|------|------|
| **SPF** | 어떤 서버가 이 도메인으로 메일을 보낼 수 있는지 |
| **DKIM** | 메일 위·변조 방지, 수신 측 신뢰 |
| **DMARC** (권장) | SPF/DKIM 실패 시 정책 (none → quarantine/reject 단계적 적용) |

- [ ] Resend 도메인 상태 **Verified**
- [ ] 전파 대기 (수 분~48시간) 후 [mail-tester.com](https://www.mail-tester.com) 등으로 점검 (선택)

---

## 3. 앱·Resend 설정 일치

| 항목 | 확인 |
|------|------|
| Django `SITE_ID` / Site 도메인 | `https://{DOMAIN}` |
| allauth·비밀번호 재설정 링크 | `https://` (프로덕션), 호스트 = `DOMAIN` |
| Resend **API Key** | web 컨테이너 env only (`RESEND_API_KEY`) |
| 발신 주소 | Resend에 등록한 도메인과 동일 |

---

## 4. 배포 후 스모크 테스트

- [ ] 신규 가입 → **인증 메일** 수신 (받은편지함, 스팸함 확인)
- [ ] 비밀번호 재설정 메일 수신
- [ ] 링크 클릭 시 로그인·인증 완료
- [ ] Gmail / Naver 메일 등 **2종 이상** 클라이언트에서 테스트

---

## 5. 문제 발생 시

| 증상 | 점검 |
|------|------|
| 스팸함만 도착 | SPF/DKIM/DMARC, 발신 도메인 일치, Resend 도메인 Verified |
| 링크 404 / CSRF | `DOMAIN`, `CSRF_TRUSTED_ORIGINS`, HTTPS 리다이렉트 |
| 발송 실패 로그 | Resend 대시보드 Logs, Django `EMAIL_*` / Anymail 설정 |

---

## 6. 운영

- Resend **무료 티어 한도**·월 발송량 모니터링
- 도메인·DNS 변경 시 이 문서부터 재점검

**관련**: 인프라 `DOMAIN` — [infrastructure.md](./infrastructure.md)
