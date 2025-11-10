# 프로젝트 구조
```
fastapi_app/
 ├─ Dockerfile
 ├─ requirements.txt
 ├─ app/
 │   ├─ main.py
 │   └─ static/
 │       ├─ index.html
 │       ├─ style.css
 │       └─ script.js
```

# 이미지 빌드
```
docker image build -t my-fastapi:demo .
```

# 컨테이너 실행
```
docker container run --name fastapi --rm -p 8000:8000 my-fastapi:demo
```

# 테스트 사이트
```
http://localhost:8000
```