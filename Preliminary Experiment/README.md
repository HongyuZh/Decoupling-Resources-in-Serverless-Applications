# README

## Version 1: Basic Implementation
0. required packages
   
    ```text
    numpy
    matplotlib
    docker   
    ```

1. build docker image

    ```shell
    export rootdir=matmul
    export image_name=$rootdir
    cd rootdir
    docker build -t $image_name .
    cd ../
    ```

2. run experiment
   
    ```shell
    python main.py -n $image_name -c [repeat times]
    ```

3. plot

    ```shell
    python plot.py -n $image_name
    ```

## Version 2: Deep Understanding of Docker

1. control memory

   - if xxx < actual required memory, the container will be killed  
   - we can set memory-swap to -1 for unlimited swap memory at the expense of performance
   
   ```shell
   docker run --memory=xxxMB --memory-swap=-1 $image_name
   ```

2. cpu control

   - `docker run --cpus=xxx $image_name` gives an unstable results. The following is my example:
   ```text
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpus 2  matmul:v1
   INFO:root:2045
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpus 2  matmul:v1
   INFO:root:1633
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpus 2  matmul:v1
   INFO:root:1527
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpus 2  matmul:v1
   INFO:root:1133
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpus 2  matmul:v1
   INFO:root:1881
   ```
   - we can optimize cpu configs using:
   ```shell
   docker run --cpu-period=100000 --cpu-quota=500000 $image_name
   ```

   ```text
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpu-period=100000 --cpu-quota=200000 matmul:v1
   INFO:root:1537
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpu-period=100000 --cpu-quota=200000 matmul:v1
   INFO:root:1825
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpu-period=100000 --cpu-quota=200000 matmul:v1
   INFO:root:1422
   (dl) zinuo@zinuo-aisig:ZINUO$ docker run --cpu-period=100000 --cpu-quota=200000 matmul:v1
   INFO:root:1537
   ```
