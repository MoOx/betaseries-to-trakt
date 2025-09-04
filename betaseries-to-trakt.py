#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import re
import json
import requests
import time

bs_api = 'https://api.betaseries.com'
bs_api_key = os.environ.get('BS_API_KEY')
bs_movie_route = '%s/movies/movie' % (bs_api)
bs_show_route = '%s/shows/display' % (bs_api)

trakt_api = 'https://api.trakt.tv'
auth_get_token_route = '%s/oauth/token' % (trakt_api)
sync_history_route = '%s/sync/history' % (trakt_api)
sync_watchlist_route = '%s/sync/watchlist' % (trakt_api)

bs_session = requests.Session()
session = requests.Session()

bs_session.headers.update({
    'Accept':     'application/json',
    'User-Agent': 'Betaseries to Trakt',
    'Connection': 'Keep-Alive',
    'X-BetaSeries-Key' : bs_api_key
})

def login_to_trakt():

    print('')
    print('Open the link in a browser and paste the pin')
    print('https://trakt.tv/oauth/authorize?response_type=code&client_id=%s&redirect_uri=urn:ietf:wg:oauth:2.0:oob' % (os.environ.get('CLIENT_ID')))
    print('')

    pin = str(input('Pin: '))

    session.headers.update({
        'Accept':     'application/json',
        'User-Agent': 'Betaseries to Trakt',
        'Connection': 'Keep-Alive'
    })

    post_data = {
        'code':          pin,
        'client_id':     os.environ.get('CLIENT_ID'),
        'client_secret': os.environ.get('CLIENT_SECRET'),
        'redirect_uri':  'urn:ietf:wg:oauth:2.0:oob',
        'grant_type':    'authorization_code'
    }

    request = session.post(auth_get_token_route, data=post_data)
    response = request.json()

    session.headers.update({
        'Content-Type':      'application/json',
        'trakt-api-version': '2',
        'trakt-api-key':     os.environ.get('CLIENT_ID'),
        'Authorization':     'Bearer ' + response["access_token"]
    })

def create_show_history(obj):
    id = obj[0]
    name = obj[1]
    status_pct = obj[4]

    try:
        output = re.search('S([0-9]+)E([0-9]+)', obj[3])
        if not output:
            print(f"⚠️  Format d'épisode invalide pour la série '{name}' (ID: {id}): {obj[3]}")
            return None
            
        last_seen_season = output.group(1)
        last_seen_episode = output.group(2)

        request = bs_session.get(bs_show_route + '?id=' + id)
        response = request.json()
        
        # Petit délai pour éviter de surcharger l'API
        time.sleep(0.1)
        
        if 'show' not in response or 'thetvdb_id' not in response['show']:
            print(f"⚠️  Série '{name}' (ID: {id}) non trouvée dans Betaseries, ignorée.")
            return None

        show = {
            'name': name,
            'ids': {
                'tvdb': response['show']['thetvdb_id']
            },
            'watched_at': 'released'
        }

        if status_pct != '100':
            show['seasons'] = []

            for s in range(0, int(last_seen_season)):
                show['seasons'].append({
                    'number': s + 1,
                    'watched_at': 'released'
                })

                if (s + 1) == int(last_seen_season):
                    show['seasons'][s]['episodes'] = []

                    for e in range(0, int(last_seen_episode)):
                        show['seasons'][s]['episodes'].append({
                            'number': e + 1,
                            'watched_at': 'released'
                        })

        return show
    except Exception as e:
        print(f"❌ Erreur lors du traitement de la série '{name}' (ID: {id}): {e}")
        return None

def create_show_watchlist(obj):
    id = obj[0]
    name = obj[1]

    try:
        request = bs_session.get(bs_show_route + '?id=' + id)
        response = request.json()
        
        # Petit délai pour éviter de surcharger l'API
        time.sleep(0.1)
        
        if 'show' not in response or 'thetvdb_id' not in response['show']:
            print(f"⚠️  Série '{name}' (ID: {id}) non trouvée dans Betaseries, ignorée.")
            return None

        show = {
            'name': name,
            'ids': {
                'tvdb': response['show']['thetvdb_id']
            }
        }

        return show
    except Exception as e:
        print(f"❌ Erreur lors du traitement de la série '{name}' (ID: {id}): {e}")
        return None

def create_movie_history(obj):
    id = obj[0]
    name = obj[1]

    try:
        request = bs_session.get(bs_movie_route + '?id=' + id)
        response = request.json()
        
        # Petit délai pour éviter de surcharger l'API
        time.sleep(0.1)
        
        if 'movie' not in response or 'tmdb_id' not in response['movie']:
            print(f"⚠️  Film '{name}' (ID: {id}) non trouvé dans Betaseries, ignoré.")
            return None

        movie = {
            'title': name,
            'ids': {
                'tmdb': response['movie']['tmdb_id']
            },
            'watched_at': 'released'
        }
        
        return movie
    except Exception as e:
        print(f"❌ Erreur lors du traitement du film '{name}' (ID: {id}): {e}")
        return None

def create_movie_watchlist(obj):
    id = obj[0]
    name = obj[1]

    try:
        request = bs_session.get(bs_movie_route + '?id=' + id)
        response = request.json()
        
        # Petit délai pour éviter de surcharger l'API
        time.sleep(0.1)
        
        if 'movie' not in response or 'tmdb_id' not in response['movie']:
            print(f"⚠️  Film '{name}' (ID: {id}) non trouvé dans Betaseries, ignoré.")
            return None

        movie = {
            'title': name,
            'ids': {
                'tmdb': response['movie']['tmdb_id']
            }
        }
        
        return movie
    except Exception as e:
        print(f"❌ Erreur lors du traitement du film '{name}' (ID: {id}): {e}")
        return None


def main():
    login_to_trakt()

    post_history_data = {
        'shows': [],
        'movies': []
    }

    post_watchlist_data = {
        'shows': [],
        'movies': []
    }

    for file_path in sys.argv[1::]:
        file = open(file_path, encoding="utf8")
        file_name = os.path.basename(file_path)
        
        print(f"📄 Traitement du fichier: {file_name}")
        
        # Compter le nombre total de lignes pour afficher la progression
        total_lines = sum(1 for line in open(file_path, encoding="utf8")) - 1  # -1 pour le header
        current_line = 0

        for row in csv.reader(file):
            # we move to next line (first is header)
            if row[0] == 'id':
                continue
                
            current_line += 1
            
            # Déterminer le type basé sur le nombre de colonnes
            # Séries: id,title,archive,episode,remaining,status,tags (7 colonnes)
            # Films: id,title,status,date (4 colonnes)
            if len(row) >= 7:
                type = 'show'
            elif len(row) == 4:
                type = 'movie'
            else:
                print(f"⚠️  Format non reconnu pour la ligne: {row}")
                continue
                
            print(f"📊 Progression: {current_line}/{total_lines} - {type}: {row[1]}")

            if type == 'show':
                status_pct = row[5]
                if status_pct == '0':
                    show = create_show_watchlist(row)
                    if show is not None:
                        post_watchlist_data['shows'].append(show)
                else:
                    show = create_show_history(row)
                    if show is not None:
                        post_history_data['shows'].append(show)

            if type == 'movie':
                status = row[2] # '2' = je ne veux pas voir, '1' = j'ai vu, '0' = je veux voir
                if status == '0':
                    movie = create_movie_watchlist(row)
                    if movie is not None:
                        post_watchlist_data['movies'].append(movie)
                elif status == '1':
                    movie = create_movie_history(row)
                    if movie is not None:
                        post_history_data['movies'].append(movie)

        file.close()

    # Post 'history' data
    request_history = session.post(sync_history_route, data=json.dumps(post_history_data))
    
    if request_history.status_code == 200 or request_history.status_code == 201:
        response_history = request_history.json()
    else:
        print(f"Error with history request: {request_history.status_code} - {request_history.text}")
        response_history = {"added": {"episodes": 0, "movies": 0}, "not_found": {"shows": [], "episodes": [], "movies": []}}

    # Wait 2 seconds to respect rate limits
    time.sleep(2)

    # Post 'watchlist' data
    request_watchlist = session.post(sync_watchlist_route, data=json.dumps(post_watchlist_data))
    
    if request_watchlist.status_code == 200 or request_watchlist.status_code == 201:
        response_watchlist = request_watchlist.json()
    else:
        print(f"Error with watchlist request: {request_watchlist.status_code} - {request_watchlist.text}")
        response_watchlist = {"added": {"shows": 0, "movies": 0}, "existing": {"shows": 0, "movies": 0}, "not_found": {"shows": [], "movies": []}}

    # Print summary

    print('\r\nMigration from Betaseries CSV files Done!')

    print('\r\n-----------------------------------------')
    print('HISTORY')

    print('\r\nAdded:')
    # print('\t %s shows' % response_history['added']['shows'])
    print('\t %s episodes' % response_history['added']['episodes'])
    print('\t %s movies' % response_history['added']['movies'])

    if response_history['not_found']['shows'] or response_history['not_found']['episodes'] or response_history['not_found']['movies']:
        print('Not found:')

        if len(response_history['not_found']['shows']):
            print('\t shows:')
            print(response_history['not_found']['shows'])

        if len(response_history['not_found']['episodes']):
            print('\t episodes:')
            print(response_history['not_found']['episodes'])

        if len(response_history['not_found']['movies']):
            print('\t movies:')
            print(response_history['not_found']['movies'])

    print('\r\n-----------------------------------------')
    print('WATCHLIST')

    print('\r\nAdded:')
    print('\t %s shows' % response_watchlist['added']['shows'])
    print('\t %s movies' % response_watchlist['added']['movies'])

    if response_watchlist['existing']['shows'] or response_watchlist['existing']['movies']:
        print('Existing:')
        if response_watchlist['existing']['shows']:
            print('\t %s shows' % response_watchlist['existing']['shows'])

        if response_watchlist['existing']['movies']:
            print('\t %s movies (the play count was incremented)' % response_watchlist['existing']['movies'])

    if response_watchlist['not_found']['shows'] or response_watchlist['not_found']['movies']:
        print('Not found:')

        if len(response_watchlist['not_found']['shows']):
            print('\t shows:')
            print(response_watchlist['not_found']['shows'])

        if len(response_watchlist['not_found']['movies']):
            print('\t movies:')
            print(response_watchlist['not_found']['movies'])


if __name__ == "__main__":
    main()
