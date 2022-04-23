'''
This file is created to show the reading process of my json file 
it is also exsit in main.py
'''
import json
import time
import requests
# read cache file and output cache dict


def open_cache(CACHE_NAME="cache.json"):
    try:
        cache_file = open(CACHE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def fetch_cache(url, cache_dict):

    if (url in cache_dict.keys()):  # the url is our unique key
        print("---cache---")
        return cache_dict[url], True
    else:
        print("---Fetching---")
        time.sleep(0.5)
        response = requests.get(url)
        return response.text, False
