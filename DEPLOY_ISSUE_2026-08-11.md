# Reflex Cloud 배포 장애 정리 (2026-08-11)

> 상태: **미해결 / Reflex 지원팀 응답 대기 중**
> 영향 범위: 프론트엔드 배포만 불가. **운영 중인 서비스와 백엔드는 정상.**

---

## 1. 문제 발생 시작

### 배경 — 무엇을 배포하려 했나

두 가지 변경을 프로덕션에 반영하려던 중이었다.

| 커밋 | 내용 |
|---|---|
| `69d21f5` | 무로그인 체험 페이지 `/demo` 추가 (포트폴리오·공모전 링크용) |
| `77d029e` | 로그인 실패 원인이던 상태 락 만료(LockExpiredError) 수정 |

### 정상 완료된 부분

- **코드**: GitHub `master`에 푸시 완료. 로컬 테스트 67개 통과.
- **백엔드(Render)**: 자동 배포 성공. `GET /recommendation/demo` 호출 시
  HTTP 200으로 추천 결과 정상 반환 (첫 응답 36초 — 무료 티어 콜드스타트).
- **로컬 동작**: `/demo` 페이지가 로그인 없이 열리고 추천 5개 표시되는 것까지 확인.

### 막힌 부분

**Reflex Cloud(프론트엔드) 배포만 실패.** 프로덕션 `/demo` 접속 시 404.

---

## 2. 해결 시도했던 것

시도한 순서대로 전부 기록한다.

| # | 시도 | 결과 |
|---|---|---|
| 1 | `reflex deploy` (출력에 `\| tail -8` 파이프) | warning 한 줄만 남고 종료 |
| 2 | `reflex deploy` (출력을 파일로 리다이렉트) | 동일 |
| 3 | `reflex deploy` (출력 자르지 않음, `python -u`) | **"Internal server error occurred"** 확인 |
| 4 | 즉시 재시도 | 같은 500 |
| 5 | 10분 후 재시도 | `app has a pending deployment` |
| 6 | 25분 후 재시도 | 동일 |
| 7 | 45분 후 재시도 | 동일 |
| 8 | `apps stop` (pending 털어내기 목적) | `a deployment, promotion, or rollback is in progress` |
| 9 | `apps start` | `no stopped deployment found` (앱은 실행 중) |
| 10 | `apps history` | **HTTP 500** |
| 11 | 대시보드에서 배포 취소 | 취소 버튼 자체가 없음 |
| 12 | 대시보드에서 Rollback | `Rollback not available` (Deploying 상태에는 비활성) |
| 13 | CLI 업그레이드 0.1.67 → 0.1.68 | 성공. 단 **취소 명령은 신버전에도 없음** |
| 14 | `apps rollback` (현재 배포 대상) | `already the app's current deployment` |
| 15 | **새 앱 이름으로 배포** | 앱 생성은 성공, **배포는 같은 500** ← 결정적 단서 |
| 16 | 새로 만든 빈 앱 삭제 | 성공 |

### 진단 과정에서 잘못 짚었던 것 (기록용)

원인을 세 번 잘못 지목했다. 모두 **출력을 `tail`/파일로 잘라 보면서 서버가 보낸
실패 메시지를 놓친 탓**이다.

1. ~~파이프가 배포 프로세스를 끊었다~~ → 파일 리다이렉트로 바꿔도 동일하게 실패
2. ~~`--envfile` 임시 파일이 사라져서~~ → 파일 복구 후에도 동일하게 실패
3. ~~Reflex Cloud 인증 만료~~ → `apps list`가 exit 0으로 정상 응답, 인증은 유효했음

**교훈**: 여러 단계를 거치는 배포 명령은 출력을 자르지 말 것.

---

## 3. 실패한 것 (= 현재 불가능한 경로)

- **배포**: 기존 앱, 신규 앱 모두 서버 500으로 실패
- **정지(stop)**: pending 때문에 거부
- **취소**: 기능 자체가 존재하지 않음 (CLI·대시보드·API 모두)
- **롤백**: 진행 중 배포에는 적용 불가
- **시간 경과 대기**: 2시간 30분 이상 지나도 pending 자동 정리 안 됨

### 취소 기능이 없다는 근거

CLI 소스(`reflex_cli/utils/hosting.py`)의 배포 관련 API 엔드포인트 전체:

```
/api/v1/deployments                            (생성)
/api/v1/deployments/{deployment_id}/status
/api/v1/deployments/{deployment_id}/build/logs
/api/v1/apps/{app_id}/deployments/{id}/rollback
/api/v1/apps/{app_id}/deployments/{id}/description
```

cancel·abort·terminate 계열 함수는 `grep` 결과 **0건**. CLI를 우회해 API를
직접 호출해도 취소할 방법이 없다.

---

## 4. 원인

### 확정된 원인

**Reflex Cloud의 배포 파이프라인 서버측 장애.**

결정적 근거는 시도 #15다. **pending 배포가 하나도 없는 완전히 새 앱**
(`naengjango-hankki-v2-demo`, `42ce8ec6-c82d-494d-a527-72ccc87b6cae`)을 만들어
배포했는데, 앱 생성과 파일 업로드는 정상이었으나 배포 단계에서 **똑같은
"Internal server error"** 가 났다.

즉 기존 앱에 걸린 pending은 **원인이 아니라 이 장애의 결과**다. 배포가 서버에서
죽으면서 상태가 `Deploying`에 갇힌 것이다.

### 부수적으로 확인된 것

- `GET /api/v1/apps/{app_id}/history` → HTTP 500 (대시보드에서는 목록이 보임)
- CLI 0.1.68에 Windows 버그 존재: 임시 파일 정리 중
  `NotADirectoryError: [WinError 267] ... backend.zip`.
  배포 실패와는 **무관한 별개 버그**(정리 단계에서 발생)

### 현재 걸려 있는 배포

| Deployment ID | 상태 | 경과 |
|---|---|---|
| `2ce7a213-cc20-4806-a5a1-398ebfa3d4ec` | Deploying (멈춤) | 2시간 30분+ |
| `912b118e-f2a7-44a8-938c-c858d1af11ad` | Deploying (멈춤) | 2시간 30분+ |
| `c0b46fa0-13b4-40f8-a858-70b634943e57` | **Current / Running** | 정상 서비스 중 |

앱 ID: `3bb3c726-1d32-4d80-bae8-7cbe9022fb67`

---

## 5. 의문점

아직 답을 못 찾은 것들이다. 지원팀 문의 시 함께 물어볼 만하다.

1. **`apps list`는 되는데 `apps history`만 500인 이유는?**
   같은 인증·같은 서버인데 특정 엔드포인트만 죽어 있다. 대시보드에서는 History가
   정상 표시되므로, CLI가 쓰는 API 경로와 대시보드 경로가 다를 가능성이 있다.

2. **멈춘 배포가 왜 자동 정리되지 않나?**
   보통 배포 파이프라인은 타임아웃을 두는데, 2시간 30분이 지나도 `Deploying`
   상태 그대로다. 타임아웃이 없거나 훨씬 길게 잡혀 있는 것으로 보인다.

3. **배포 취소 기능이 아예 없는 이유는?**
   사용자가 잘못된 배포를 시작했을 때 되돌릴 수단이 없다는 뜻인데, 호스팅
   서비스로서는 이례적이다. 로드맵에 있는지 확인이 필요하다.

4. **`rollback`은 왜 pending 검사를 통과하나?**
   `deploy`와 `stop`은 "pending 있음"으로 거부되는데, `rollback`은 그 검사를
   통과하고 "이미 현재 배포"라는 다른 이유로 거부됐다. 검사 조건이 명령마다
   다르다면, 롤백으로 pending을 우회할 여지가 있는지 확인 가치가 있다.

5. **이 장애가 계정 단위인가, 플랫폼 전체인가?**
   신규 앱에서도 실패했으므로 최소한 계정 단위다. 전체 장애라면 상태 페이지에
   공지가 있을 텐데 확인하지 못했다.

---

## 6. 해소를 위해 생각하고 있는 방안

리스크가 낮은 순서다.

### A. 지원팀 응답 대기 — **현재 진행 중, 권장**

Support chat으로 문의 접수 완료(응답 대기). 취소 API가 존재하지 않는 이상
서버 쪽에서 정리받는 것이 정공법이다.

문의 내용에 아래를 추가하면 처리가 빨라질 것이다.

```
Update: This is not just stuck deployments — deployment is broken account-wide.
I created a brand-new app (naengjango-hankki-v2-demo,
42ce8ec6-c82d-494d-a527-72ccc87b6cae) with no pending deployments.
Upload succeeded, but deploy still failed with "Internal server error occurred"
(deployment de16e01d-30d9-47ca-9c85-8405aa80d081).
Also GET /api/v1/apps/{app_id}/history still returns 500.
Tested with reflex-hosting-cli 0.1.68 (upgraded from 0.1.67).
```

### B. 로컬 데모 화면 녹화 — **지금 바로 가능**

배포와 무관하게 `/demo`는 로컬에서 정상 동작한다. 포트폴리오·공모전 제출용
스크린샷이나 화면 녹화를 미리 확보해두면, 배포 지연이 길어져도 자료는 남는다.

### C. Render로 프론트엔드 이전 — **반나절 이상 지연 시**

이미 백엔드를 Render에 올려두었고 계정·저장소 연동·`render.yaml`이 갖춰져 있다.
Reflex 앱도 Python 프로세스이므로 웹 서비스로 띄울 수 있다.

- 장점: 계정 추가 불필요, Reflex Cloud 장애와 무관
- 단점: 무료 티어 512MB에서 Reflex 프론트+백엔드가 뜨는지 미검증,
  15분 유휴 후 콜드스타트

### D. 허깅페이스 Spaces (Gradio) — **비용 감수 가능할 때**

세션 초반에 만들어둔 Gradio 데모 코드와 3.2MB 경량 DB가 `hf_space/`에 이미
커밋되어 있다. 다만 무료 계정은 Gradio Space 생성이 막혀 있어(HF가 402 응답,
"free cpu-basic requires PRO") **PRO 구독 월 $9**이 필요하다.

### 권하지 않는 것

- **기존 앱 삭제 후 재생성**: 신규 앱조차 배포가 안 되는 게 확인됐다.
  URL만 잃고 얻을 게 없다.
- **구버전으로 롤백**: 성공해도 서비스가 후퇴하고, 이후 배포가 계속 막히면
  구버전에 갇힌다. 지금은 최신 버전이 정상 서비스 중이라 상태가 나빠질 뿐이다.

---

## 7. 현재 상태 요약

| 항목 | 상태 |
|---|---|
| 코드 (GitHub) | 정상 — `69d21f5`, `77d029e` 푸시 완료 |
| 테스트 | 67개 전부 통과 |
| 백엔드 (Render) | **정상 배포·동작** — `/recommendation/demo` 200 응답 |
| 프론트엔드 (Reflex Cloud) | 기존 버전 정상 서비스 중, **신규 배포 불가** |
| 사용자 영향 | **없음** — 기존 기능 모두 정상 |
| 미반영 | `/demo` 페이지, 로그인 락 수정 |

pending이 해소되면 **배포 명령 한 번**으로 두 변경이 함께 반영된다.
