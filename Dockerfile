ARG FLASK_PORT

FROM python:3.11.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN chmod +x start.sh

CMD ["./start.sh"]
