import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_dedicated_pages(url):
    resp = requests.get(url)
    resp.encoding = resp.apparent_encoding
    
    soup = BeautifulSoup(resp.text, 'html.parser')

    ankers = soup.select("td.'views-field-field-std-document-number' a")

    pages = []
    for anker in ankers:
        dedicated_page_url = urljoin(url , anker['href'])
        pages.append(dedicated_page_url)

    return pages

def get_pages(index_url):

    url = '{}?page={}'.format(index_url, 0)
    pages0 = get_dedicated_pages(url)

    url = '{}?page={}'.format(index_url, 1)
    pages1 = get_dedicated_pages(url)

    pages = pages0 + pages1

    return pages
    
index_url = 'https://standards.nasa.gov/all-standards'
pages = get_pages(index_url)

import time
import os
import json

info_list = []
for page in pages:
    resp = requests.get(page)
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, 'html.parser')
    ankers = soup.select("div.field--name-field-pub-upload-public-std a[type='application/pdf']")
    if len(ankers) > 1:
        print("[WARNING1]")
        print(page)
        print(ankers)
        print('---')
        continue
    elif len(ankers) == 0:
        print("[WARNING2]")
        print(page)
        continue

    url = ankers[0]['href']
    url = urljoin(index_url, url)
    name = os.path.split(url)[1]
    print(url)
    print(name)

    file = requests.get(url)

    fd = open(name, 'wb')
    fd.write(file.content)
    fd.close()

    info = {'name': name, 'web_page': page, 'doc_page': url}
    info_list.append(info)

    fd = open("info.json", 'w')
    fd.write(json.dumps(info_list))
    fd.close()

    print(info_list)
    
    time.sleep(15)


    
