import zipfile
import json
import requests
from tqdm import tqdm


def arc_to_dict(arc_path):
    out = {}
    with zipfile.ZipFile(arc_path, 'r') as arc:
        for file in arc.namelist():
            out[file.split('.')[0]] = json.loads(arc.read(file).decode('utf-8'))
    return out


def extract_info(tweet_json):
    # in case retweeted reference the original tweet
    if 'retweeted_status' in tweet_json:
        tweet_json = tweet_json['retweeted_status']
    info = {
        'id': tweet_json['id_str'],
        'user_name': tweet_json.get('user_name'),
        'user_id': tweet_json.get('user_id'),
        'text': tweet_json["full_text"],
        'link': f"https://twitter.com/empty/status/{tweet_json['id_str']}",
        'media_urls': [],
    }
    extended = tweet_json.get('extended_entities', [])

    if "media" in extended:
        for x in extended["media"]:
            if x["type"] == "photo":
                url = x.get("media_url", x['media_url_https'])
                info['media_urls'].append((url, x['type']))
            elif x["type"] in ["video", "animated_gif"]:
                variants = x["video_info"]["variants"]
                variants.sort(key=lambda xx: xx.get("bitrate", 0))
                url = variants[-1]["url"].rsplit("?tag")[0]
                info['media_urls'].append((url, x['type']))
    return info


def create_html(metadata, aws_mode=False):
    def _tweet_block(tweet_meta):
        tweet_html = "<div id=\"{tweet_id}\" class=\"tweet\"><div>{tweet_text} {tweet_link}</div> {tweet_media}</div> <hr>"

        tweet_text_html = f"<text>{tweet_meta['text']}</text>"
        tweet_link_html = f"<a href=\"{tweet_meta['link']}\">[link]</a>"
        tweet_media_html = ''
        for i, media in enumerate(tweet_meta['media_urls']):
            media_url = media[0] if not aws_mode else f"tweets/{tweet_meta['id']}/{i}.{media[0].split('.')[-1]}"
            if media[1] == 'video':
                tweet_media_html += f"<iframe class=\"vid\" src={media_url} loading=\"lazy\"></iframe>"
            elif media[1] == 'photo':
                tweet_media_html += f"<img class=\"image\" src={media_url} loading=\"lazy\"/>"
            else:
                tweet_media_html += f"<video autoplay loop muted inline class=\"gif\" src={media_url} loading=\"lazy\"/>"

        return tweet_html.format(
            tweet_id=tweet_meta['id'],
            tweet_text=tweet_text_html,
            tweet_link=tweet_link_html,
            tweet_media=tweet_media_html
        )

    html = "<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>"
    head = """<style>
    .tweet{
    }
    .image {
    height: 90vh;
    width: 90vw;
    object-fit: contain;
    }
    .vid {
    height: 90vh;
    width: 90vw;
    object-fit: contain;
    }
    .gif {
    height: 90vh;
    width: 90vw;
    object-fit: contain;
    }
    </style>
    """
    body = ''
    for tw in metadata:
        body += _tweet_block(tw)
    return html.format(
        head=head,
        body=body
    )


def _get_file_size(url):
    url_head = requests.head(url)
    try:
        s = int(url_head.headers['content-length'])
    except KeyError:
        print(url)
        s = 0
    return s


if __name__ == '__main__':
    data_path = "downloads/Aug-2022.zip"
    tweets_json = arc_to_dict(data_path)
    parsed_tweets = []
    for tweet_id in tweets_json.keys():
        parsed_tweets.append(extract_info(tweets_json[tweet_id]))
    with open(data_path[:-3]+'html', 'w', encoding='utf-8') as out:
        out_html = create_html(parsed_tweets)
        out.write(out_html)
