# 폴더 구조

```
fastapi-mysql-demo/
├─ app/
│  ├─ main.py              # FastAPI 앱 (DB 연결, 라우팅)
│  ├─ requirements.txt     # fastapi, uvicorn, pymysql, cryptography, jinja2
│  ├─ Dockerfile           # 앱 컨테이너용
│  ├─ templates/
│  │  └─ index.html        # 아주 단순한 HTML
│  └─ static/
│     ├─ style.css         # 간단 CSS
│     └─ app.js            # 간단 JS
└─ db/
   └─ init.sql             # 최초 기동 시 자동 실행될 SQL (테이블/샘플데이터)
```

# 실행 및 종료
```
docker compose up --build -d     # 빌드 후 백그라운드 실행
docker compose logs -f app       # 앱 로그 팔로우
docker compose ps                # 상태 확인
docker compose down              # 종료 (볼륨 유지)
# 볼륨까지 삭제(초기화 필요 시)
docker compose down -v
```

# 테스트
- 브라우저 : http://localhost:8000/