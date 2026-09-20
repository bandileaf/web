# CLAUDE.md

## 프로젝트

- 이 저장소는 웹 서비스(정적 HTML)를 만들고 GitHub Pages 로 배포하는 곳이다.
- 원격 저장소: `git@github.com:bandileaf/web.git` (SSH), 브랜치는 `main`.
- 배포 주소: https://bandileaf.github.io/web/
- push 하면 약 30초~2분 안에 배포에 반영된다.

## 작업 방식

- 결과 확인은 로컬이 아니라 배포된 사이트에서 하므로, 파일을 수정하면 바로 commit 하고 **즉시 push** 한다. 별도로 묻지 않는다.
- 이 규칙은 이 프로젝트에서 전역 `CLAUDE.md` 의 "push 지시가 없으면 commit 까지만" 규칙보다 우선한다.
- push 전 보안 점검은 그대로 지킨다. `git diff origin/main..HEAD` 를 review 해서 아래가 포함되어 있으면 push 하지 않고 내용을 알린다.
  - 비밀번호, API 키, 토큰, 개인키(`.ssh`, `NPKI`, `.pem`, `.env` 등)
  - 주민등록번호, 증명서 등 개인 서류와 연락처 같은 개인정보
- 저장소는 public 이므로 올라간 내용은 모두 공개된다는 점을 항상 염두에 둔다.
- push 후에는 배포 반영에 시간이 걸리니 확인 요청 시 `Ctrl+F5` 로 새로고침하도록 안내한다.

## 구조

- 진입점은 `index.html` 이다. 빌드 도구 없이 HTML, CSS, JS 로만 구성한다.
- 외부 의존은 Google Fonts 정도로 최소화한다.
