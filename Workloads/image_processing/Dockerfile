FROM python
COPY function.py function.py
COPY ops.py ops.py
RUN pip3 install minio && pip3 install PIL
RUN docker run -d -p 9000:9000 -p 9001:9001 --name minio1 \
    -e "MINIO_ACCESS_KEY=IMAGEPROCESSING" \
    -e "MINIO_SECRET_KEY=DECOUPLINGRESOURCE" \
    minio/minio server /data --console-address ":9001"
CMD python3 function.py