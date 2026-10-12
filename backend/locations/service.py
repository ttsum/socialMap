import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class AmapError(Exception):
    pass


def request_amap(path, params):
    key = os.getenv('AMAP_API_KEY', '')
    if not key:
        raise AmapError('高德地图服务未配置 AMAP_API_KEY')
    query = dict(params, key=key, output='json')
    url = os.getenv('AMAP_BASE_URL', 'https://restapi.amap.com/v3').rstrip('/') + path + '?' + urlencode(query)
    try:
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise AmapError('高德地图服务暂时不可用') from exc
    if payload.get('status') != '1':
        raise AmapError(payload.get('info') or '高德地图返回错误')
    return payload


def search(keywords, city=''):
    payload = request_amap('/place/text', {'keywords': keywords, 'city': city, 'offset': 10, 'page': 1, 'extensions': 'base'})
    items = []
    for item in payload.get('pois', []):
        location = (item.get('location') or '').split(',')
        if len(location) != 2:
            continue
        try:
            lng, lat = float(location[0]), float(location[1])
        except ValueError:
            continue
        items.append({'name': item.get('name', ''), 'address': item.get('address') or '', 'city': item.get('cityname') or city, 'lng': lng, 'lat': lat})
    return items


def geocode(address, city=''):
    payload = request_amap('/geocode/geo', {'address': address, 'city': city})
    item = (payload.get('geocodes') or [None])[0]
    if not item or not item.get('location'):
        return None
    lng, lat = item['location'].split(',')
    return {'name': address, 'address': item.get('formatted_address') or address, 'city': item.get('city') or city, 'lng': float(lng), 'lat': float(lat)}
