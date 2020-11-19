#!/usr/bin/env python3

import os, requests


def main():
    print('itch.io:')
    resp = requests.get('https://itch.io/api/1/key/my-games',
                        headers={'Authorization': 'Bearer ' + os.environ['ITCHIO_API_KEY']})
    resp.raise_for_status()
    for game in resp.json()['games']:
        if game['title'] == 'Undying Dusk':
            print('  Views:', game['views_count'])
            print('  Downloads:', game['downloads_count'])
            print('  Purchases:', game['purchases_count'])
    print()

    print('GitHub:')
    resp = requests.get('https://api.github.com/repos/Lucas-C/undying-dusk/releases')
    resp.raise_for_status()
    for release in resp.json():
        print(release['tag_name'], 'downloads:')
        for asset in release['assets']:
            print('  ', asset['name'], asset['download_count'])
        print()

if __name__ == '__main__':
    main()
