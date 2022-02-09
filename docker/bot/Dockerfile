FROM python:3.10
COPY . /bot_folder
WORKDIR /bot_folder
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "./run_bot.py" ]