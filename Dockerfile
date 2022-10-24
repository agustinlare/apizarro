FROM python:3.8

RUN mkdir /apizarro
RUN chmod -R 777 /apizarro

ENV PORT=8080 \
    FLASK_APP="app.py" \
    FLASK_RUN_HOST="0.0.0.0" \
    FLASK_RUN_PORT=8080 \
    CLUSTER_CONFIG_FILE="./conf/ocpconfig.conf"

COPY . /apizarro

RUN apt update ; apt install wget curl tcpdump -y -q

EXPOSE $PORT
WORKDIR /apizarro 

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

CMD [ "app.py" ]
ENTRYPOINT [ "python3" ]