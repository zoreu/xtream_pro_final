# -*- coding: utf-8 -*-
from urllib.parse import urlparse
import requests
import base64



def last_raw(url):
    try:
        path_url = urlparse(url).path
        try:
            base = path_url.split('raw/')[0]
        except:
            base = path_url.split('refs/')[0]
        try:
            base = base.split('refs/')[0]
        except:
            pass
        file = path_url.split('/heads')[1]
        file_name = file.split('/main')[1]
        cookies = {'_locale': 'pt-br',
                'logged_in': 'no',
                'preferred_color_mode': 'light'}  
        lastest_commit_url = 'https://github.com{0}latest-commit{1}'.format(base,file)
        referer = 'https://github.com{0}blob{1}'.format(base,file)
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0', 'Referer': referer, 'x-requested-with': 'XMLHttpRequest'}
        api = requests.get(lastest_commit_url,headers=headers,cookies=cookies).json()
        commit = api['oid']
        raw = 'https://raw.githubusercontent.com{0}{1}{2}'.format(base,commit,file_name)
    except:
        raw = ''
    return raw


# def last_gist(url):
#     try:
#         parse_url = urlparse(url)
#         host = '{0}://{1}'.format(parse_url.scheme, parse_url.netloc)
#         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0', 'Accept-language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'}
#         r = requests.get(url,headers=headers)
#         soup = BeautifulSoup(r.text, 'html.parser')
#         link = soup.find('div', class_ = lambda x: x and x.startswith('file-actions')).find('a').get('href', '')
#         raw = host + link
#     except:
#         raw = ''
#     return raw




