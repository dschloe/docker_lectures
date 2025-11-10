# 베이스 이미지 지정
FROM python:3.12.5

# 컨테이너 실행 시 실행될 명령어 지정
CMD ["/usr/local/bin/python3", "-m", "http.server", "8000"]