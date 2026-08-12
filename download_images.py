import os
import urllib.request
import json
import ssl

def download_wiki_image(query, filename):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={query}&prop=pageimages&format=json&pithumbsize=800"
    req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            pages = data['query']['pages']
            for page_id in pages:
                if 'thumbnail' in pages[page_id]:
                    img_url = pages[page_id]['thumbnail']['source']
                    img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    with urllib.request.urlopen(img_req, context=ctx) as img_resp, open(f'app/static/img/{filename}', 'wb') as f:
                        f.write(img_resp.read())
                        print(f"Downloaded {filename} from {img_url}")
                    return
        print(f"Failed to find image for {query}")
    except Exception as e:
        print(f"Error for {query}: {e}")

download_wiki_image('3D_printing', 'printer.jpg')
download_wiki_image('Multimeter', 'multimeter.jpg')
