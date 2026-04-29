"""
sync_tweets.py — X API v2 で最新ツイートを取得し tweets/data.json に追記
GitHub Actions から呼び出される。環境変数 X_BEARER_TOKEN が必要。
"""

import json, os, sys
import requests
from datetime import datetime, timezone
from pathlib import Path

BEARER_TOKEN = os.environ.get('X_BEARER_TOKEN', '')
USERNAME = 'rmaruy'
DATA_FILE = Path('tweets/data.json')


def headers():
    return {'Authorization': f'Bearer {BEARER_TOKEN}'}


def get_user_id():
    r = requests.get(
        f'https://api.twitter.com/2/users/by/username/{USERNAME}',
        headers=headers()
    )
    r.raise_for_status()
    return r.json()['data']['id']


def fetch_tweets(user_id, since_id=None):
    params = {
        'max_results': 100,
        'tweet.fields': 'created_at,text',
        'exclude': 'retweets',
    }
    if since_id:
        params['since_id'] = since_id

    r = requests.get(
        f'https://api.twitter.com/2/users/{user_id}/tweets',
        headers=headers(),
        params=params
    )
    r.raise_for_status()
    return r.json().get('data', [])


def main():
    if not BEARER_TOKEN:
        print("Error: X_BEARER_TOKEN が設定されていません")
        sys.exit(1)

    # 既存データ読み込み
    existing = []
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)

    since_id = existing[0]['id'] if existing else None

    print(f"最新ツイートID: {since_id or '(初回取得)'}")
    user_id = get_user_id()
    raw = fetch_tweets(user_id, since_id)

    if not raw:
        print("新しいツイートはありませんでした")
        return

    new_tweets = []
    for t in raw:
        try:
            dt = datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            dt = datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        dt = dt.replace(tzinfo=timezone.utc)

        new_tweets.append({
            'id':         t['id'],
            'text':       t['text'],
            'created_at': dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'date':       dt.strftime('%Y-%m-%d'),
            'url':        f'https://x.com/{USERNAME}/status/{t["id"]}',
        })

    merged = new_tweets + existing
    merged.sort(key=lambda x: x['created_at'], reverse=True)

    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"✓ {len(new_tweets)} 件追加（合計 {len(merged)} 件）")


if __name__ == '__main__':
    main()
