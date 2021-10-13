from minio import Minio

client = Minio("192.168.122.1:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)

for bucket in client.list_buckets():
    for obj in client.list_objects(bucket.name):
        client.remove_object(bucket.name, obj.object_name)
    client.remove_bucket(bucket.name)
