import zipfile
import json


def arc_to_dict(arc_path):
    out = {}
    with zipfile.ZipFile(arc_path, 'r') as arc:
        for file in arc.namelist():
            out[file.split('.')[0]] = json.loads(arc.read(file).decode('utf-8'))
    return out


def extract_info(tweet_json):
    info = {
        'id': tweet_json['id_str'],
        'text': tweet_json["full_text"],
        'link': f"https://twitter.com/empty/status/{tweet_json['id_str']}",
        'media_urls': [],
    }
    extended = tweet_json.get('extended_entities', [])

    if "media" in extended:
        for x in extended["media"]:
            if x["type"] == "photo":
                url = x["media_url"]
                info['media_urls'].append((url, x['type']))
            elif x["type"] in ["video", "animated_gif"]:
                variants = x["video_info"]["variants"]
                variants.sort(key=lambda x: x.get("bitrate", 0))
                url = variants[-1]["url"].rsplit("?tag")[0]
                info['media_urls'].append((url, x['type']))
    return info


def create_html(metadata):
    def _tweet_block(tweet_meta):
        tweet_html = "<div id=\"{tweet_id}\" class=\"tweet\"><div>{tweet_text} {tweet_link}</div> {tweet_media}</div> <hr>"

        tweet_text_html = f"<text>{tweet_meta['text']}</text>"
        tweet_link_html = f"<a href=\"{tweet_meta['link']}\">[link]</a>"
        tweet_media_html = ''
        for media in tweet_meta['media_urls']:
            if media[1] == 'video':
                tweet_media_html += f"<iframe class=\"vid\" src={media[0]} loading=\"lazy\"></iframe>"
            elif media[1] == 'photo':
                tweet_media_html += f"<img class=\"image\" src={media[0]} loading=\"lazy\"/>"
            else:
                tweet_media_html += f"<video autoplay loop muted inline class=\"gif\" src={media[0]} loading=\"lazy\"/>"

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


if __name__ == '__main__':
    data_path = "downloads/Aug-2022.zip"
    tweets_json = arc_to_dict(data_path)
    parsed_tweets = []
    for tweet_id in tweets_json.keys():
        parsed_tweets.append(extract_info(tweets_json[tweet_id]))
    with open(data_path[:-3]+'html', 'w', encoding='utf-8') as out:
        out_html = create_html(parsed_tweets)
        out.write(out_html)
