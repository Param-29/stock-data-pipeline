FROM godatadriven/pyspark

COPY * ./


RUN echo $PWD
RUN ls $PWD
RUN pip install -r requirements.txt
RUN export GOOGLE_APPLICATION_CREDENTIALS="/gcs_key/key.json"
ENTRYPOINT [ "python", "complete_flow.py" ]