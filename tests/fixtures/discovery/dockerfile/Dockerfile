FROM python:3.12-slim
WORKDIR /app
COPY . .
USER 10001
HEALTHCHECK CMD python -c "print('ok')"
CMD ["python", "-m", "sample"]
