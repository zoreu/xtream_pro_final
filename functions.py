# -*- coding: utf-8 -*-
import json
import base64
import requests
from urllib.parse import urlparse, urlencode, parse_qs
from config import config
from github import last_raw
import requests
import unicodedata

def fix_b64(b64str):
    if not '=' in b64str:
        b64str += "=" * (-len(b64str) % 4)
    return b64str

def remove_accents(text):
    """Remove acentos de uma string."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def get_base_url():
    """Obtém a URL base do servidor."""
    github_url = last_raw(config['hostimage'])
    r = requests.get(github_url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'})
    host = r.text
    host = host.replace(' ', '').replace('\n', '').replace('\r', '')
    if host.endswith('/'):
        host = host[:-1]
    return host

def get_image_url(image_url):
    """Concatena a URL base com a URL da imagem."""
    base_url = 'https://da5f663b4690-proxyimage.baby-beamup.club/proxy-image/?url='
    if image_url:
        image_url = str(image_url).strip()
    else:
        image_url = ''
    if image_url:
        image_url = base_url + image_url
    return image_url

def get_user_data(user_conf):
    """Decodifica e processa os dados do usuário."""
    try:
        user_conf = fix_b64(user_conf)
        retrieved_data = json.loads(base64.b64decode(user_conf).decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
        return "Error while parsing URL"

    obj = {}
    if isinstance(retrieved_data, dict):
        domain_name = urlparse(retrieved_data.get('BaseURL', '')).hostname or "unknown"
        base_url = retrieved_data.get('BaseURL', '')
        # id_prefix = (
        #     domain_name[0]
        #     + domain_name[len(domain_name) // 2]
        #     + domain_name[-1]
        #     + ":"
        # )
        id_prefix = (
            domain_name[0]
            + domain_name[len(domain_name) // 2]
            + domain_name[-1]
        )        
        obj = {
            'baseURL': base_url,
            'domainName': domain_name,
            'idPrefix': id_prefix,
            'username': retrieved_data.get('username'),
            'password': retrieved_data.get('password'),
        }
    elif 'http' in user_conf:
        url = user_conf
        parsed_url = urlparse(url)
        query_string = parsed_url.query or "unknown"
        base_url = f"{parsed_url.scheme}://{parsed_url.hostname}" or "unknown"
        domain_name = parsed_url.hostname or "unknown"
        # id_prefix = (
        #     domain_name[0]
        #     + domain_name[len(domain_name) // 2]
        #     + domain_name[-1]
        #     + ":"
        # )
        id_prefix = (
            domain_name[0]
            + domain_name[len(domain_name) // 2]
            + domain_name[-1]
        )        
        if not query_string or not base_url:
            return {'result': "URL is invalid or missing queries!"}

        query_params = parse_qs(query_string)
        obj = {
            'baseURL': base_url,
            'domainName': domain_name,
            'idPrefix': id_prefix,
            **query_params,
        }

    if all(key in obj for key in ['username', 'password', 'baseURL']):
        return obj

    print("Error while parsing!")
    return {}

def fix_prefix(prefix):
    if ':' in prefix:
        prefix = prefix.replace(':', '')
    return prefix

def make_curl_request(url, params=None):
    """Faz uma requisição HTTP usando a biblioteca requests."""
    if params is None:
        params = {}
    query_string = urlencode(params)
    final_url = f"{url}?{query_string}" if query_string else url

    try:
        response = requests.get(
            final_url,
            timeout=20,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
        )
        return response.text, response.status_code
    except requests.RequestException as e:
        print(f"cURL Error: {e}")
        return None, 0

def get_manifest(user_conf):
    """Gera o manifesto do addon."""
    obj = get_user_data(user_conf)
    if not obj:
        return {'error': "Invalid user data"}

    # Fetch VOD Categories
    vod_response, vod_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': 'get_vod_categories',
    })
    vod_categories = json.loads(vod_response) if vod_status == 200 else []
    movie_catalog = [cat['category_name'] for cat in vod_categories if isinstance(vod_categories, list)]

    # Fetch Series Categories
    series_response, series_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': 'get_series_categories',
    })
    series_categories = json.loads(series_response) if series_status == 200 else []
    series_catalog = [cat['category_name'] for cat in series_categories if isinstance(series_categories, list)]

    # Fetch Live Categories
    live_response, live_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': 'get_live_categories',
    })
    live_categories = json.loads(live_response) if live_status == 200 else []
    live_catalog = [cat['category_name'] for cat in live_categories if isinstance(live_categories, list)]

    prefix = fix_prefix(obj['idPrefix'])


    manifest = {
        'id': f"org.community.{obj['domainName']}" or "org.community.xtreampro",
        'version': config['version'],
        'name': f"{obj['domainName']} | {config['title']}",
        'logo': config['logo'],
        'description': f"access {obj['domainName']} IPTV with this addon!",
        'idPrefixes': [prefix],
        'resources': ["catalog", "meta", "stream"],
        'types': ["movie", "series", "tv"],
        'behaviorHints': {'configurable': True, 'configurationRequired': False},
        'catalogs': [
            {
                'id': f"{prefix}_movie",
                'type': "movie",                
                'name': obj['domainName'] + ' - Movies',
                "extra": [
                    {"name": "genre", "isRequired": False, "options": movie_catalog},
                    {"name": "search", "isRequired": False}
                ]
            },
            {
                'id': f"{prefix}_series",
                'type': "series",
                'name': obj['domainName'] + ' - Séries',
                "extra": [
                    {"name": "genre", "isRequired": False, "options": series_catalog},
                    {"name": "search", "isRequired": False}
                ]
            },
            {
                'id': f"{prefix}_tv",
                'type': "tv",                
                'name': obj['domainName'] + ' - TV',
                "extra": [
                    {"name": "genre", "isRequired": False, "options": live_catalog},
                    {"name": "search", "isRequired": False}
                ]
            }
        ]
    }    


    return manifest

def search_catalog(url, type, query):
    """Realiza uma busca no catálogo com base no tipo e no termo de pesquisa."""
    obj = get_user_data(url)
    if not obj:
        return []

    # Determinar ação para obter streams
    stream_action = "get_vod_streams" if type == "movie" else (
        "get_series" if type == "series" else "get_live_streams"
    )

    # Fazer a requisição para obter todos os itens do tipo especificado
    catalog_response, catalog_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': stream_action,
    })
    catalog_data = json.loads(catalog_response) if catalog_status == 200 else []
    metas = []

    prefix = fix_prefix(obj['idPrefix'])

    # Filtrar itens com base no termo de busca (case-insensitive)
    query = query.lower()
    for item in catalog_data:
        name = item.get('name', "").lower()
        name_no_accents = remove_accents(name)
        query_no_accents = remove_accents(query.lower())
        name3 = name_no_accents.replace('&', 'e').replace(' ', '').replace('-', '').replace('_', '')
        query3 = query_no_accents.replace('&', 'e').replace(' ', '').replace('-', '').replace('_', '')
        if query in name or query_no_accents in name_no_accents or query3 in name3:
            id_ = item['series_id'] if type == "series" else item['stream_id']
            poster = item['cover'] if type == "series" else item.get('stream_icon', "")
            poster_shape = "square" if type == "tv" else "poster"

            metas.append({
                'id': f"{prefix}:{id_}",
                'type': type,
                'name': item.get('name', ""),
                'poster': get_image_url(poster) or "",
                'posterShape': poster_shape,
                'imdbRating': item.get('rating', 0.0),
                'year': item.get('year', 0),
                'genres': [item.get('genre', '')],
                'description': item.get('plot', "")
            })

    return metas

def get_catalog_global(url, type):
    """Obtém o catálogo completo com base no tipo (movie, series, tv), pegando a primeira categoria disponível."""
    obj = get_user_data(url)
    if not obj:
        return []

    # Ação de categoria e de stream
    category_action = (
        "get_vod_categories" if type == "movie" else
        "get_series_categories" if type == "series" else
        "get_live_categories"
    )
    stream_action = (
        "get_vod_streams" if type == "movie" else
        "get_series" if type == "series" else
        "get_live_streams"
    )

    # Buscar categorias
    category_response, category_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': category_action,
    })
    categories = json.loads(category_response) if category_status == 200 else []

    # Seleciona a primeira categoria disponível
    category_id = None
    if isinstance(categories, list) and categories:
        category_id = categories[0].get('category_id')

    if not category_id:
        return []

    # Buscar conteúdo da categoria
    catalog_response, catalog_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': stream_action,
        'category_id': category_id,
    })
    catalog_data = json.loads(catalog_response) if catalog_status == 200 else []
    metas = []

    prefix = fix_prefix(obj['idPrefix'])

    for item in catalog_data:
        id_ = item['series_id'] if type == "series" else item['stream_id']
        name = item.get('name', "")
        poster = item['cover'] if type == "series" else item.get('stream_icon', "")
        poster_shape = "square" if type == "tv" else "poster"

        metas.append({
            'id': f"{prefix}:{id_}",
            'type': type,
            'name': name,
            'poster': get_image_url(poster) or "",
            'posterShape': poster_shape,
            'imdbRating': item.get('rating', 0.0),
            'year': item.get('year', 0),
            'genres': [item.get('genre', '')],
            'description': item.get('plot', "")
        })

    return metas


def get_catalog(url, type, genre):
    """Obtém o catálogo com base no tipo e gênero."""
    obj = get_user_data(url)
    if not obj:
        return []

    # Determinar ação para obter categorias
    category_action = "get_vod_categories" if type == "movie" else (
        "get_series_categories" if type == "series" else "get_live_categories"
    )

    # Buscar ID da categoria
    category_response, category_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': category_action,
    })
    categories = json.loads(category_response) if category_status == 200 else []
    category_id = next((cat['category_id'] for cat in categories if cat['category_name'] == genre), None)

    if not category_id:
        return []

    # Determinar ação para obter streams
    stream_action = "get_vod_streams" if type == "movie" else (
        "get_series" if type == "series" else "get_live_streams"
    )

    catalog_response, catalog_status = make_curl_request(f"{obj['baseURL']}/player_api.php", {
        'username': obj['username'],
        'password': obj['password'],
        'action': stream_action,
        'category_id': category_id,
    })
    catalog_data = json.loads(catalog_response) if catalog_status == 200 else []
    metas = []

    prefix = fix_prefix(obj['idPrefix'])

    for item in catalog_data:
        id_ = item['series_id'] if type == "series" else item['stream_id']
        name = item.get('name', "")
        poster = item['cover'] if type == "series" else item.get('stream_icon', "")
        poster_shape = "square" if type == "tv" else "poster"

        metas.append({
            'id': f"{prefix}:{id_}",
            'type': type,
            'name': name,
            'poster': get_image_url(poster) or "",
            'posterShape': poster_shape,
            'imdbRating': item.get('rating', 0.0),
            'year': item.get('year', 0),
            'genres': [item.get('genre', '')],
            'description': item.get('plot', "")
        })

    return metas

def get_meta(url, type, id):
    """Obtém metadados com base no tipo e ID."""
    obj = get_user_data(url)
    if not obj:
        return []

    stream_id = id.split(":")[1]

    # Determinar ação e parâmetros para buscar metadados
    meta_action = "get_vod_info" if type == "movie" else (
        "get_series_info" if type == "series" else "get_live_streams"
    )
    request_id = "vod_id" if type == "movie" else (
        "series_id" if type == "series" else "stream_id"
    )

    params = {
        'username': obj['username'],
        'password': obj['password'],
        'action': meta_action,
    }
    if type != "tv":
        params[request_id] = stream_id

    meta_response, meta_status = make_curl_request(f"{obj['baseURL']}/player_api.php", params)
    meta_data = json.loads(meta_response) if meta_status == 200 else []

    if not meta_data:
        return {}
    
    prefix = fix_prefix(obj['idPrefix'])

    # Construir resposta com metadados e streams
    if type == "movie":
        return {
            'id': f"{prefix}:{stream_id}",
            'type': type,
            'name': meta_data['info'].get('name', ""),
            'poster': get_image_url(meta_data['info'].get('cover_big', "")),
            'background': get_image_url(meta_data['info'].get('backdrop_path', [""])[0]),
            'description': meta_data['info'].get('description', ""),
            'releaseInfo': meta_data['info'].get('releasedate', "").split("-")[0]
        }
    elif type == "series":
        try:
            year = int(meta_data['info'].get('releaseDate', "").split("-")[0])
        except:
            year = 0
        try:
            imdb_rating = float(meta_data['info'].get('rating', ""))
        except:
            imdb_rating = 0.0        
        meta = {
            'id': f"{prefix}:{stream_id}",
            'type': type,
            'name': meta_data['info'].get('name', ""),
            'year': year, 
            'imdbRating': imdb_rating,                       
            'poster': meta_data['info'].get('backdrop_path', [""])[0],
            #'logo': meta_data['info'].get('backdrop_path', [""])[0],
            'background': meta_data['info'].get('backdrop_path', [""])[0],
            'genres': ['Séries'],
            'trailers': [],
            'description': meta_data['info'].get('plot', ""),
            'videos': []
        }

        # Processar episódios
        for season, episodes in meta_data.get('episodes', {}).items():
            for episode in episodes:
                meta['videos'].append({
                    'id': f"{prefix}:{stream_id}:{episode.get('season')}:{episode.get('episode_num')}",
                    'name': episode.get('title', f"Episode {episode.get('episode_num', '')}"),
                    'season': episode.get('season'),
                    'number': episode.get('episode_num'),
                    'episode': episode.get('episode_num'),
                    'thumbnail': get_image_url(episode.get('info', {}).get('movie_image', ""))
                })                   

        return meta
    elif type == "tv":
        for item in meta_data:
            if int(item['stream_id']) == int(stream_id):
                return {
                    'id': f"{prefix}:{item['stream_id']}",
                    'name': item.get('name', ""),
                    'type': type,
                    'background': "https://raw.githubusercontent.com/zoreu/xtreampro/refs/heads/main/bgwallpaper.jpg",
                    'poster': get_image_url(item.get('stream_icon', "")),
                    'logo': get_image_url(item.get('stream_icon', ""))
                }

    return {}

def get_stream(url, type, id):
    """Obtém metadados com base no tipo e ID."""
    obj = get_user_data(url)
    if not obj:
        return []

    if id.count(':') == 3:
        stream_id = id.split(':')[1]
        #stream_id = id.split(':')[2]
        season = id.split(':')[2]
        episode = id.split(':')[3]
    elif id.count(':') == 1:
        stream_id = id.split(':')[1]
    else:
        return {'streams': []}

    # Determinar ação e parâmetros para buscar metadados
    meta_action = "get_vod_info" if type == "movie" else (
        "get_series_info" if type == "series" else "get_live_streams"
    )
    request_id = "vod_id" if type == "movie" else (
        "series_id" if type == "series" else "stream_id"
    )

    params = {
        'username': obj['username'],
        'password': obj['password'],
        'action': meta_action,
    }
    if type != "tv":
        params[request_id] = stream_id

    meta_response, meta_status = make_curl_request(f"{obj['baseURL']}/player_api.php", params)
    meta_data = json.loads(meta_response) if meta_status == 200 else []

    if not meta_data:
        return {'streams': []}

    # Construir resposta com metadados e streams
    if type == "movie":
        return {
            'streams': [{
                'name': 'Xtream Pro',
                'title': meta_data['info'].get('name', "Stream"),
                'url': f"{obj['baseURL']}/movie/{obj['username']}/{obj['password']}/{stream_id}.mp4",
            }],
        }
    elif type == "series":
        for season_, episodes in meta_data.get('episodes', {}).items():
            for episode_ in episodes:
                if int(episode_.get('season')) == int(season) and int(episode_.get('episode_num')) == int(episode):
                    return {
                        'streams': [{
                            'name': 'Xtream Pro',
                            'title': episode_.get('title', f"Episode {episode_.get('episode_num', '')}"),
                            'url': f"{obj['baseURL']}/series/{obj['username']}/{obj['password']}/{episode_['id']}.mp4",
                        }],
                    }      
    elif type == "tv":
        for item in meta_data:
            if int(item['stream_id']) == int(stream_id):
                return {
                    'streams': [{
                        'name': 'Xtream Pro',
                        'title': item.get('name', "Live Channel"),
                        'url': f"{obj['baseURL']}/live/{obj['username']}/{obj['password']}/{item['stream_id']}.m3u8",
                    }],
                }

    return {'streams': []}