# This code is buggy!

from time import time

from minio import Minio
from PIL import Image

import ops

minioClient = Minio('127.0.0.1:9000',
                    access_key='IMAGEPROCESSING',
                    secret_key='DECOUPLINGRESOURCE',
                    secure=False)

FILE_NAME_INDEX = 2


def image_processing(file_name, image_path):
    path_list = []
    start = time()
    with Image.open(image_path) as image:
        tmp = image
        path_list += ops.flip(image, file_name)
        path_list += ops.rotate(image, file_name)
        path_list += ops.filter(image, file_name)
        path_list += ops.gray_scale(image, file_name)
        path_list += ops.resize(image, file_name)

    latency = time() - start
    return latency, path_list


def func():
    bucket_name = 'bucket'
    object_name = 'image'

    download_path = '/tmp/image.jpg'

    minioClient.fget_object(bucket_name, object_name, download_path)

    latency, path_list = image_processing(object_name, download_path)

    print(path_list)

    # for upload_path in path_list:
    #     minioClient.fput_object(bucket_name, object_name,
    #                             upload_path.split("/")[FILE_NAME_INDEX])

    return latency


if __name__ == '__main__':

    func()
