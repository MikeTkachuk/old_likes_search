import boto3
from generate_html import arc_to_dict, extract_info, create_html
import requests
import json
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import os
import io


BUCKET_NAME = ''
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""

session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                aws_secret_access_key=AWS_SECRET_KEY)
s3 = session.client('s3')


def _path_exists(client, path_):
    obj_list_ = client.list_objects_v2(Bucket=BUCKET_NAME,
                                       Prefix=path_,
                                       MaxKeys=5)
    return obj_list_['KeyCount']


def _create_path(client, path_):
    if path_[-1] != '/':
        path_ += '/'
    client.put_object(Bucket=BUCKET_NAME, Key=path_)


def create_bucket_structure(client):
    if not _path_exists(client, "tweets"):
        _create_path(client, "tweets")
    if not _path_exists(client, "backups"):
        _create_path(client, "backups")


def upload_tweet(tweet_meta):
    # new session for multiprocessing
    session_ = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                     aws_secret_access_key=AWS_SECRET_KEY)
    client = session_.client('s3')

    # check if already uploaded media
    tweet_path = f"tweets/{tweet_meta['id']}/"
    if _path_exists(client, tweet_path) > 1:
        return False

    for i, media in enumerate(tweet_meta['media_urls']):
        media_request = requests.get(media[0], stream=True)
        client.upload_fileobj(media_request.raw,
                              BUCKET_NAME,
                              tweet_path + str(i) + '.' + media[0].split('.')[-1])

    client.upload_fileobj(io.BytesIO(json.dumps(tweet_meta).encode('utf-8')),
                          BUCKET_NAME,
                          tweet_path + 'info.json')

    return True


def backup_arc(client, arc_path):
    create_bucket_structure(client)

    tweets_json = arc_to_dict(arc_path)
    parsed = [extract_info(tweets_json[tweet_id]) for tweet_id in sorted(tweets_json.keys())]

    with Pool(cpu_count()) as p:
        success_list = list(tqdm(
            p.imap(upload_tweet, parsed)
        ))

    html = create_html(parsed, aws_mode=True)
    client.upload_fileobj(io.BytesIO(html.encode('utf-16')),
                          BUCKET_NAME,
                          f"backups/{os.path.split(arc_path)[-1].split('.')[0]}.html")
    return success_list


if __name__ == "__main__":
    arc = "downloads/2022.zip"
    ret = backup_arc(s3, arc)
    print(sum(ret)/len(ret), len(ret), sum(ret))