import re

import requests
from bs4 import BeautifulSoup


vgm_url = 'https://ca.news.yahoo.com'


def parse(vgm_url):
    html_text = requests.get(vgm_url).text
    soup = BeautifulSoup(html_text, 'html.parser')
    semi_results = soup.find(id='item-0')
    all_imgs = [img["src"] for img in semi_results.select("img")]
    news_link = ([
        link["href"] if link["href"][0:3] == 'http' else 'https://ca.style.yahoo.com' + link["href"] for link in semi_results.select("a", class_='js-content-viewer')])
    texts = [result.text for result in semi_results.select("a", class_='js-content-viewer')]
    result = []
    for el in range(len(all_imgs)):
        result += [all_imgs[el], news_link[el], texts[el]]
    return result


def download_track(count, track_element):
    # Get the title of the track from the HTML element
    track_title = track_element.text.strip().replace('/', '-')
    download_url = '{}{}'.format(vgm_url, track_element['href'])
    file_name = '{}_{}.mid'.format(count, track_title)

    # Download the track
    r = requests.get(download_url, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)

    # Print to the console to keep track of how the scraping is coming along.
    # print('Downloaded: {}'.format(track_title, download_url))


if __name__ == '__main__':
    soup = parse(vgm_url)
    attrs = {
        'href': re.compile(r'https://s.yimg.com/os/creatr-uploaded-images:\/\/')
    }

    # tracks = soup.find_all('a', attrs=attrs, string=re.compile(r'^((?!\().)*$'))
    # tracks = soup.find_all(class_='js-content-viewer')
    with open('result.html', 'w') as file:
        file.write(str(soup))
