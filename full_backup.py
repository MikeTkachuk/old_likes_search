import os
import io
import datetime
import shutil
import threading
import zipfile
from pathlib import Path

import requests
import json
from multiprocessing import Pool, cpu_count
import boto3
from tqdm import tqdm
import warnings

from generate_html import arc_to_dict, extract_info, create_html

BUCKET_NAME = "twitter-backup4"
PROFILE_NAME = "tmg"

session = boto3.session.Session(profile_name=PROFILE_NAME)
s3 = session.client('s3')


def _num_files(client, path_):
    """
    Return number of objects with the prefix provided.
        Can't be more than 5 (4 media + info.json)
    :param client:
    :param path_:
    :return:
    """
    obj_list_ = client.list_objects_v2(Bucket=BUCKET_NAME,
                                       Prefix=path_,
                                       MaxKeys=5)
    return obj_list_['KeyCount']


def _create_path(client, path_):
    if path_[-1] != '/':
        path_ += '/'
    client.put_object(Bucket=BUCKET_NAME, Key=path_)


def _delete_recursive(client, prefix):
    keys = client.list_objects_v2(Bucket=BUCKET_NAME,
                                  Prefix=prefix)
    if keys['KeyCount'] > 5:
        raise RuntimeError("Attempted to delete >5 files")
    client.delete_objects(Bucket=BUCKET_NAME,
                          Delete={
                              'Objects': [{"Key": obj["Key"]} for obj in keys["Contents"]],
                          },
                          )


def create_bucket_structure(client):
    if not _num_files(client, "tweets"):
        _create_path(client, "tweets")
    if not _num_files(client, "backups"):
        _create_path(client, "backups")


def upload_tweet(tweet_meta):
    # new session for multiprocessing
    session_ = boto3.session.Session(profile_name=PROFILE_NAME)
    client = session_.client('s3')

    # check if already uploaded and filecount matches config
    tweet_path = f"tweets/{tweet_meta['id']}/"
    if _num_files(client, tweet_path) == len(tweet_meta['media_urls']) + 1:
        return False
    upload_report = f"{tweet_meta['id']}"
    for i, media in enumerate(tweet_meta['media_urls']):
        content_type = 'video/mp4' if media[0].endswith('mp4') else 'image/' + media[0].split('.')[-1]
        content_type = {'ContentType': content_type}
        media_filename = str(i) + '.' + media[0].split('.')[-1]
        media_key = tweet_path + media_filename
        upload_report += " " + media_filename
        media_request = requests.get(media[0], stream=True)
        client.upload_fileobj(media_request.raw,
                              BUCKET_NAME,
                              media_key,
                              ExtraArgs=content_type)
        uploaded_size = client.head_object(Bucket=BUCKET_NAME,
                                           Key=media_key)["ContentLength"]
        if not uploaded_size:
            _delete_recursive(client, tweet_path)
            print(f"Invalid response from {media[0]} in {tweet_meta['id']}")
            return False

    client.upload_fileobj(io.BytesIO(json.dumps(tweet_meta).encode('utf-8')),
                          BUCKET_NAME,
                          tweet_path + 'info.json',
                          ExtraArgs={'ContentType': 'application/json'})
    upload_report += " info.json"
    return upload_report


# @warnings.deprecated()
def update_index_html(client):
    backup_pag = client.get_paginator("list_objects_v2")
    backup_resp = backup_pag.paginate(Bucket=BUCKET_NAME, Prefix="backups/", PaginationConfig={"PageSize": 1000})
    backups = []
    for p in backup_resp:
        backups.extend([x['Key'] for x in p['Contents'] if x['Key'].endswith('.html')])

    html_start = """<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css" charset="utf-8">
    <script src="main.js" charset="utf-8">
    </script>
</head>

<body>
<div id="controls">
        <button id="shuffle" onclick="shuffleTweets();">Shuffle</button>
        <button id="top" onclick="topFunction();">Top</button>
        <button id="video_pause" onclick="pauseAll();">Pause all</button>
        <input type="number" id="navigate_param" min="0" max="100" step="5">
        <button id="navigate" onclick="scrollTo();">Go</button>
</div>
<div id="menu"><ol>"""
    html_end = """

</ol></div>
<div style=\"background-color:#909090; height: 2vh\"></div>
<div id="tweets_div"></div>
</body>
</html>"""
    for b in backups:
        html_start += f"<li><a onclick=\"pick_backup('{b.split('/')[-1]}');\">{b.split('/')[-1]}</a></li>\n"

    html = html_start + html_end
    s3.upload_fileobj(io.BytesIO(html.encode('utf-16')),
                      BUCKET_NAME,
                      f"index.html",
                      ExtraArgs={'ContentType': 'text/html'}
                      )


# @warnings.deprecated()
def backup_arc(client, arc_path):
    """
    For uploading archives produced by download_data.download_likes.
    Checks bucket structure, parses metadata from archive and uploads media.
    Updates generated html.
    :param client:
    :param arc_path:
    :return:
    """
    create_bucket_structure(client)

    tweets_json = arc_to_dict(arc_path)
    parsed = [extract_info(tweets_json[tweet_id]) for tweet_id in sorted(tweets_json.keys())]

    with Pool(cpu_count()-1) as p:
        success_list = list(tqdm(
            p.imap(upload_tweet, parsed), total=len(parsed)
        ))

    html = create_html(parsed, aws_mode=True)
    client.upload_fileobj(io.BytesIO(html.encode('utf-16')),
                          BUCKET_NAME,
                          f"backups/{os.path.split(arc_path)[-1].split('.')[0]}.html",
                          ExtraArgs={'ContentType': 'text/html'})
    update_index_html(client)
    return success_list


def get_tweet_iterator_from_response(response_dict):
    entries = response_dict['data']['user']['result']['timeline']['timeline']['instructions'][0]['entries']
    for entry in entries:
        if 'itemContent' in entry['content']:
            result = entry['content']['itemContent']['tweet_results']['result']
            if 'legacy' in result:
                tweet_dict = result['legacy']
            else:
                tweet_dict = result['tweet']['legacy']
            try:  # try get user name
                user_name = result['core']['user_results']['result']['legacy']['name']
                user_id = result['core']['user_results']['result']['rest_id']
                tweet_dict['user_name'] = user_name
                tweet_dict['user_id'] = user_id
            except KeyError:
                pass
            yield tweet_dict


class ObjListCache:
    def __init__(self, path="tweets_list_cache.txt"):
        self.path = path
        self.file_content = s3.get_object(Bucket=BUCKET_NAME, Key=path)['Body'].read().decode('utf-8')

    def update(self, value, sync=False):
        self.file_content += value
        if sync:
            self.sync()

    def sync(self):
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=self.path,
            Body=self.file_content,
            ContentType='text/plain'
        )

    def reindex(self, sync=False):
        paginator = s3.get_paginator('list_objects_v2')
        # List all objects
        page_iter = paginator.paginate(Bucket=BUCKET_NAME, Prefix="tweets/")
        groups = {}  # group_id -> list of filenames
        for page in page_iter:
            for obj in page.get('Contents', []):
                key: str = obj['Key']
                # skip keys that end with slash prefix placeholder
                if key.endswith('/'):
                    continue
                parts = key.split('/')
                group, filename = parts[-2], parts[-1]
                groups.setdefault(group, []).append(filename)

        self.file_content = ""
        for group in groups:
            files = sorted(groups[group])
            line = f"{group} " + " ".join(files)
            self.file_content += line + "\n"

        if sync:
            self.sync()


class ObjMetadataCache(ObjListCache):
    def __init__(self, path="tweets_metadata_cache.txt"):
        super().__init__(path)

    def reindex(self, sync=False):
        paginator = s3.get_paginator('list_objects_v2')
        # List all objects
        page_iter = paginator.paginate(Bucket=BUCKET_NAME, Prefix="tweets/")
        lock = threading.Lock()
        threads = []
        self.file_content = ""

        def read_worker(path):
            string = s3.get_object(Bucket=BUCKET_NAME, Key=path)['Body'].read().decode('utf-8')
            with lock:
                self.file_content += string + "\n"

        for page in page_iter:
            for obj in page.get('Contents', []):
                key: str = obj['Key']
                # skip keys that end with slash prefix placeholder
                if key.endswith('info.json'):
                    t = threading.Thread(target=read_worker, args=(key,))
                    t.start()
                    threads.append(t)
        for t in threads:
            t.join()

        if sync:
            self.sync()


def interactive_response_upload():
    """
    Should be run from python console to avoid input length limit
    :return:
    """

    print("Running full backup in interactive mode from fetch responses.")
    os.chdir(Path(__file__).parent)
    temp_dir = Path('downloads/_temp')
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=False)
    today_str = datetime.datetime.today().strftime('%d-%b-%Y')
    archive_name = f'{today_str}.zip'
    list_cache = ObjListCache()
    meta_cache = ObjMetadataCache()
    print("Archive name: ", archive_name)
    print("Input json response one at a time. Provide empty line to exit")

    with zipfile.ZipFile('downloads/' + archive_name, 'w') as arc:
        with Pool(cpu_count()-1) as p:
            while True:
                try:
                    response = input("Enter response: ")
                    if not response:
                        break
                    to_upload = []
                    for tweet in get_tweet_iterator_from_response(json.loads(response)):
                        tweet_file_path = temp_dir / f'{tweet["id_str"]}.json'
                        with open(tweet_file_path, 'w') as f:
                            json.dump(tweet, f)
                        arc.write(tweet_file_path, arcname=tweet_file_path.name)
                        tweet_file_path.unlink()
                        to_upload.append(extract_info(tweet))
                    upload_reports = list(tqdm(
                        p.imap(upload_tweet, to_upload), total=len(to_upload)
                    ))
                    list_cache.update("\n".join([r for r in upload_reports if r]) + "\n", sync=True)
                    meta_cache.update("\n".join([json.dumps(t) for t in to_upload]) + "\n", sync=True)
                    # success_stats.append(upload_tweet(extract_info(tweet)))  # todo: debug what this line does, maybe remove
                    print("# tweets provided:", len(upload_reports),
                          " # tweets uploaded:", sum([bool(s) for s in upload_reports]))

                except Exception as e:
                    print("Encountered exception while processing the last entry: ", e)
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    interactive_response_upload()
