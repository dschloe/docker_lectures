# 폴더 구조

```
tips-ml-compose/
├─ compose.yaml
├─ .env
├─ db/
│  └─ init.sql                  # 스키마(컬럼에 source/created_at 포함)
├─ loader/
│  ├─ Dockerfile
│  └─ loader.py                 # seaborn.tips 적재(초기 데이터, source='initial')
└─ app/
   ├─ Dockerfile
   ├─ requirements.txt
   └─ streamlit_app.py          # 대시보드(신규 입력→재학습, KPI, 혼동행렬, 리포트, ROC/PR)
```

# 실행
- 개발(코드 동기화) 모드
```
docker compose --profile dev up --build -d
docker compose logs -f app
```

- 운영(이미지 고정) 모드
    + 코드 수정 시 즉시 반영(Streamlit가 자동 리로드)
```
docker compose up --build -d
```

- 종료
```
docker compose down          # 데이터 유지
docker compose down -v       # 볼륨까지 제거(초기화)
```