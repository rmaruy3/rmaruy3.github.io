"""
parse_tweets.py — tweet.js → tweets/data.json

使い方:
  python scripts/parse_tweets.py /path/to/tweet.js

複数ファイルある場合（tweet.js, tweet-part1.js ...）:
  python scripts/parse_tweets.py /path/to/tweet.js /path/to/tweet-part1.js
"""

import json, re, sys
from datetime import datetime, timezone
from pathlib import Path


def load_tweet_js(filepath):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    # "window.YTD.tweets.partN = " プレフィックスを除去
    content = re.sub(r'^window\.YTD\.tweets\.part\d+\s*=\s*', '', content.strip())
    return json.loads(content)


def parse_tweets(data, skip_retweets=True, skip_replies=False):
    tweets = []
    for item in data:
        t = item.get('tweet', item)
        text = t.get('full_text', '')

        if skip_retweets and text.startswith('RT @'):
            continue
        if skip_replies and text.startswith('@'):
            continue

        tweet_id = t.get('id_str') or t.get('id', '')
        created_at_raw = t.get('created_at', '')

        try:
            dt = datetime.strptime(created_at_raw, '%a %b %d %H:%M:%S +0000 %Y')
            dt = dt.replace(tzinfo=timezone.utc)
            iso = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            date = dt.strftime('%Y-%m-%d')
        except Exception:
            iso = created_at_raw
            date = ''

        tweets.append({
            'id':         tweet_id,
            'text':       text,
            'created_at': iso,
            'date':       date,
            'url':        f'https://x.com/rmaruy/status/{tweet_id}',
        })

    tweets.sort(key=lambda x: x['created_at'], reverse=True)
    return tweets


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_tweets.py /path/to/tweet.js [tweet-part1.js ...]")
        sys.exit(1)

    all_data = []
    for path in sys.argv[1:]:
        print(f"読み込み中: {path}")
        all_data.extend(load_tweet_js(path))

    tweets = parse_tweets(all_data)

    out = Path('tweets/data.json')
    out.parent.mkdir(exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(tweets)} 件を {out} に書き出しました")
    print(f"  最古: {tweets[-1]['date']}  最新: {tweets[0]['date']}")


if __name__ == '__main__':
    main()
