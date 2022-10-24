FROM python:3.8-slim
RUN mkdir /pethealthpptx
ADD . /pethealthpptx

WORKDIR /pethealthpptx
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"] 