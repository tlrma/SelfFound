# GitHub 사용 가이드

> SLAF 프로젝트 팀원용 깃허브 사용법 정리
> 처음 협업하시는 분도 따라할 수 있게 작성했습니다.

---

## 목차

1. [깃허브가 뭔지](#1-깃허브가-뭔지)
2. [처음 한 번만 할 셋업](#2-처음-한-번만-할-셋업)
3. [저장소 만들기 + 팀원 초대](#3-저장소-만들기--팀원-초대)
4. [내 컴퓨터에 가져오기](#4-내-컴퓨터에-가져오기)
5. [매일 쓰는 명령어](#5-매일-쓰는-명령어)
6. [브랜치 전략](#6-브랜치-전략)
7. [Pull Request 작성법](#7-pull-request-작성법)
8. [자주 만나는 상황](#8-자주-만나는-상황)
9. [절대 하지 말 것](#9-절대-하지-말-것)
10. [처음 일주일 체크리스트](#10-처음-일주일-체크리스트)

---

## 1. 깃허브가 뭔지

- **Git**: 코드 변경 이력을 관리하는 도구 (내 컴퓨터에서 동작)
- **GitHub**: Git 저장소를 인터넷에 올려서 팀원과 공유하는 서비스

비유:
- Git = 파일에 "저장" 누르는 것 (단, 이력이 다 남음)
- GitHub = 그 파일을 클라우드에 올려서 같이 보는 것

---

## 2. 처음 한 번만 할 셋업

### (1) 계정 + 설치

- [github.com](https://github.com) 가입
- Git 설치
  - Ubuntu: `sudo apt install git`
  - Windows: [git-scm.com](https://git-scm.com) 에서 다운로드
  - Mac: `brew install git`

### (2) 본인 정보 등록

커밋에 본인 이름이 박히도록 등록합니다.

```bash
git config --global user.name "서진"
git config --global user.email "your-email@example.com"
```

### (3) SSH 키 등록 (추천)

매번 비밀번호 안 치게 SSH 키 만들어 등록하세요.

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
# Enter 3번 (기본 경로, 비밀번호 없이)

cat ~/.ssh/id_ed25519.pub
# 출력된 내용 전체 복사
```

GitHub → 우상단 프로필 → **Settings** → **SSH and GPG keys** → **New SSH key** → 붙여넣기

---

## 3. 저장소 만들기 + 팀원 초대

### 저장소 생성 (한 명만)

1. GitHub에서 우상단 **+** → **New repository**
2. 이름: `slaf-system`
3. **Private** 선택 (학교 프로젝트면 비공개 추천)
4. **Add a README file** 체크
5. **Create repository**

### 팀원 초대

- **Settings** → **Collaborators** → **Add people**
- 상대방 GitHub 아이디 또는 이메일 입력
- 초대받은 사람은 이메일 알림 확인 후 수락

### Main 브랜치 보호 설정 (중요)

`main`에 실수로 직접 푸시하지 못하게 막아둡니다.

- **Settings** → **Branches** → **Add branch protection rule**
- Branch name pattern: `main`
- ✅ Require a pull request before merging
- ✅ Require approvals (1명)

---

## 4. 내 컴퓨터에 가져오기

```bash
cd ~/projects                          # 작업 폴더로 이동
git clone https://github.com/tlrma/SelfFound.git
cd SelfFound
```

이제 이 폴더 안에서 작업하면 됩니다.

---

## 5. 매일 쓰는 명령어

이 흐름이 90%예요. 외워두세요.

### 작업 시작할 때

```bash
git checkout dev                       # dev 브랜치로 이동
git pull origin dev                    # 최신 코드 받기
git checkout -b feature/내작업          # 새 브랜치 생성하고 이동
```

### 작업 중간/끝에

```bash
git status                             # 뭐가 바뀌었는지 확인
git add .                              # 변경사항 전부 스테이징
git commit -m "[backend] 신고 API 추가"  # 커밋 (저장)
git push origin feature/내작업          # 깃허브에 올리기
```

### GitHub에서

1. **Pull Request** (PR) 생성
2. `feature/내작업` → `dev` 로 머지 요청
3. 팀원이 리뷰 → Approve → Merge
4. 머지된 브랜치는 삭제

### 다음 작업 시작

```bash
git checkout dev
git pull origin dev                    # 머지된 내용 받기
git checkout -b feature/다음작업
```

### 명령어 빠른 참조표

| 명령어 | 하는 일 |
|---|---|
| `git status` | 현재 상태 확인 |
| `git add .` | 모든 변경사항 스테이징 |
| `git add 파일명` | 특정 파일만 스테이징 |
| `git commit -m "메시지"` | 커밋 (저장) |
| `git push` | 깃허브에 올리기 |
| `git pull` | 깃허브에서 받기 |
| `git checkout 브랜치명` | 브랜치 이동 |
| `git checkout -b 새브랜치명` | 새 브랜치 생성 + 이동 |
| `git branch` | 브랜치 목록 |
| `git log --oneline` | 커밋 이력 보기 |
| `git diff` | 변경사항 자세히 보기 |

---

## 6. 브랜치 전략

```
main ────────────●────────────●───────  ← 시연 직전만 머지
                 ↑            ↑
dev  ──●──●──●──●──●──●──●──●─────────  ← 통합 브랜치
       ↑     ↑     ↑     ↑
       feature/매칭-알고리즘
             feature/dobot-제어
                   fix/카메라-버그
```

### 브랜치 이름 규칙

- `main` — 항상 동작하는 상태 유지
- `dev` — 통합 브랜치, 평소 작업의 기준점
- `feature/짧은-설명` — 새 기능 (`feature/매칭-알고리즘`)
- `fix/짧은-설명` — 버그 수정 (`fix/dobot-피킹-실패`)
- `docs/짧은-설명` — 문서만 수정 (`docs/api-명세-업데이트`)

### 커밋 메시지 규칙

`[모듈] 한글 설명` 형식

좋은 예:
- `[backend] 신고 접수 API 추가`
- `[ros] Dobot pickup action 서버 구현`
- `[vision] YOLO 추론 노드 작성`
- `[frontend] 신고 폼 동의 체크박스 추가`
- `[docs] API 명세 업데이트`

나쁜 예:
- ❌ `수정`
- ❌ `버그 픽스`
- ❌ `작업중`
- ❌ `ㅁㄴㅇㄹ`

---

## 7. Pull Request 작성법

PR은 "내 작업 검토해 줘"라는 요청이에요.

### PR 만드는 법

1. `git push` 후 GitHub 저장소 페이지로 가면 노란 박스에 **Compare & pull request** 버튼이 뜸
2. 클릭 → 제목/설명 작성 → **Create pull request**

### PR 제목/설명 템플릿

```markdown
## 무엇을 했나
- 신고 접수 API 구현
- 동의 체크박스 검증 로직 추가

## 어떻게 테스트했나
- Postman으로 POST /api/reports/ 호출 확인
- 동의 체크 안 하면 400 응답 확인

## 리뷰 포인트
- 동의 검증 위치가 시리얼라이저인지 뷰인지 의견 듣고 싶음

## 관련 이슈
- Closes #12
```

### 리뷰어 (팀원)는

- **Files changed** 탭에서 변경 내용 확인
- 줄별로 코멘트 남기기 가능
- 선택: **Approve** / **Request changes** / **Comment**

### 머지 후

- 머지된 브랜치는 GitHub에서 자동으로 삭제 권장
- 로컬에서도 삭제: `git branch -d feature/내작업`

---

## 8. 자주 만나는 상황

### 상황 A: 다른 사람이 먼저 머지해서 충돌

내 브랜치에 dev의 최신 내용을 가져와야 해요.

```bash
git checkout feature/내작업
git pull origin dev
# 충돌(conflict) 발생 시 파일에 <<<<<<< 표시됨
# 직접 수정 후
git add .
git commit -m "[merge] dev 머지"
git push
```

### 충돌 마크 읽는 법

```
<<<<<<< HEAD
내가 작성한 내용
=======
다른 사람이 작성한 내용
>>>>>>> dev
```

이 중 어느 쪽을 살릴지 결정하고, `<<<<<<<`, `=======`, `>>>>>>>` 마크는 전부 삭제해야 합니다.

### 상황 B: 실수로 잘못 커밋

```bash
git reset --soft HEAD~1                # 마지막 커밋 취소 (변경사항은 유지)
```

### 상황 C: 작업 중인데 다른 브랜치로 가야 할 때

```bash
git stash                              # 현재 변경사항 임시 저장
git checkout 다른브랜치
# 작업 후 돌아와서
git checkout feature/내작업
git stash pop                          # 임시 저장 복원
```

### 상황 D: 깃허브에 잘못된 파일을 올림

```bash
git rm 파일명
git commit -m "[chore] 잘못 올린 파일 삭제"
git push
```

> ⚠️ `.env` 같은 비밀 파일을 푸시했다면 즉시 비밀번호/API 키 재발급하세요.
> Git 이력에 영원히 남기 때문에 단순 삭제로는 해결 안 됩니다.

### 상황 E: 어떤 파일이 변경됐는지 모르겠을 때

```bash
git status                             # 변경된 파일 목록
git diff                               # 변경 내용 상세히
git diff 파일명                         # 특정 파일만
```

### 상황 F: 커밋했지만 푸시 전에 메시지 바꾸고 싶을 때

```bash
git commit --amend -m "[backend] 새 메시지"
```

> ⚠️ 이미 푸시한 커밋은 amend 하지 마세요. 협업이 꼬입니다.

---

## 9. 절대 하지 말 것

1. ❌ **`.env` 파일 커밋** — 비밀번호, API 키 노출
2. ❌ **`main`에 직접 푸시** — 항상 PR로
3. ❌ **`--force` 푸시** (`git push -f`) — 다른 사람 작업이 날아갈 수 있음
4. ❌ **큰 바이너리 파일 그대로 푸시** — 모델 `.pt`, SLAM 맵 등은 Git LFS 또는 별도 공유
5. ❌ **"수정함" 같은 의미 없는 커밋 메시지**
6. ❌ **다른 사람 브랜치에 강제로 변경** — 본인 브랜치만 만지기

---

## 10. 처음 일주일 체크리스트

### 둘 다

- [ ] 깃허브 계정 만들기
- [ ] Git 설치, `user.name`/`user.email` 설정
- [ ] SSH 키 생성 + 깃허브에 등록
- [ ] 저장소 clone
- [ ] 첫 `feature/` 브랜치 만들어서 README 한 줄 수정 → PR 한 번 연습
- [ ] 서로 리뷰하고 머지해보기

### 한 명 (저장소 생성자)

- [ ] 저장소 생성 (Private, README 포함)
- [ ] 팀원을 Collaborator로 초대
- [ ] `main` branch protection rule 설정
- [ ] `dev` 브랜치 생성 후 default branch로 변경
- [ ] `.gitignore`, `.env.example`, `README.md`, `docs/` 초기 커밋

---

## 부록: 추천 도구

명령어가 익숙해질 때까지 GUI 도구도 같이 쓰면 편해요.

| 도구 | 특징 |
|---|---|
| **GitHub Desktop** | 가장 쉬움, 초보 추천 |
| **VS Code 내장 Git** | 코딩하면서 바로 커밋 |
| **GitKraken** | 시각화 잘 됨 (학생 무료) |
| **SourceTree** | 무료, 기능 많음 |

명령어와 GUI 둘 다 익혀두시면 좋아요. 명령어는 빠르고, GUI는 변경사항 시각화에 유리합니다.

---

## 부록: 더 알아두면 좋은 것

시간 되면 알아보세요:

- **Issues 탭** — 할 일/버그를 카드처럼 관리
- **Projects 탭** — 칸반 보드처럼 작업 관리
- **GitHub Actions** — 자동 테스트, 빌드, 배포
- **Releases** — 버전 태그 + 시연 영상 첨부
- **Wiki** — 긴 문서 정리

---

## 문제 생기면

1. 일단 `git status` 쳐서 현재 상태 확인
2. 구글에 영어로 검색 (한글보다 결과 훨씬 많음)
3. 팀원에게 물어보기
4. 망쳐도 괜찮아요. Git은 웬만하면 복구 가능합니다.

> 💡 가장 안전한 방법: 뭔가 이상하면 **변경사항을 다른 곳에 복사해두고** 시도해보세요.
