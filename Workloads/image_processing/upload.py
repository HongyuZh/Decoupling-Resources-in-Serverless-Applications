from minio import Minio

if __name__ == '__main__':
    minioClient = Minio('127.0.0.1:9000',
                        access_key='IMAGEPROCESSING',
                        secret_key='DECOUPLINGRESOURCE',
                        secure=False)

    if not minioClient.bucket_exists('bucket'):
        minioClient.make_bucket("bucket", "cn-north-1")

    minioClient.fput_object("bucket", "image", "./test_image.jpg")

    print('done')
