
FROM ubuntu:latest

RUN apt-get update -y
RUN apt-get install -y python3.10 python3-pip

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt 

EXPOSE 8080

CMD ["python3", "server.py"]		