# README
0. required packages
   
    ```text
    numpy
    matplotlib
    docker   
    ```

1. build docker image

    ```shell
    export image_name=ex5:v2
    docker build -t $image_name .
    ```

2. run experiment
    
    ```shell
    python main.py -n $image_name -c [repeat times]
    ```

3. plot

    ```shell
    python plot.py -n $image_name
    ```
