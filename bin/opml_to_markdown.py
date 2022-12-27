import xml.etree.ElementTree as ET

import requests
from pyfranc import franc


def load_description(rss_url) -> str:
    try:
        resp = requests.get(rss_url)
        resp.encoding = 'utf-8'
        file = ET.ElementTree(ET.fromstring(resp.text))
        return file.getroot().find("./channel/description").text
    except:
        return ''


def parse_opml():
    excluded = [
        242181, 2372947, 2497670, 3545543, 3778211, 3804606
    ]
    podcasts = {
        'pol': [],
        'eng': []
    }
    file = ET.parse("overcast.opml")
    for item in file.getroot().findall("./body/outline/"):
        website = item.attrib['htmlUrl']
        if website and int(item.attrib['overcastId']) not in excluded:
            title = item.attrib['title']
            description = load_description(item.attrib['xmlUrl']) \
                .replace('''<br /><hr><p style='color:grey; font-size:0.75em;'> Hosted on Acast. See <a style='color:grey;' target='_blank' rel='noopener noreferrer' href='https://acast.com/privacy'>acast.com/privacy</a> for more information.</p>''', '') \
                .replace('''<br><p><br></p>''', '') \
                .replace(''' || ''', ' / ') \
                .strip()
            lang_code = next(t[0] for t in (franc.lang_detect(title + ' ' + description)) if t[0] in ['eng', 'pol'])
            podcasts[lang_code].append({
                'title': title, 'website': website, 'description': description

            })
    return podcasts


def print_lang(podcasts: list, lang: str, label: str):
    print(f'## {label}')
    print()
    per_lang = podcasts[lang]
    per_lang.sort(key = lambda p: p['title'])
    for podcast in per_lang:
        print(f'### [{podcast["title"]}]({podcast["website"]})')
        print()
        print(podcast['description'])
        print()


def run():
    podcasts = parse_opml()
    print_lang(podcasts, 'eng', 'English')
    print_lang(podcasts, 'pol', 'Polskie')


run()