#! /usr/bin/env python3
# coding: utf-8

import os
from tqdm import tqdm
import logging as lg
import pandas as pd
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import pdfplumber
import pdfplumber
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib3.connectionpool import log as urllibLogger
import requests
from pdfminer.high_level import extract_text
from io import BytesIO


lg.basicConfig(level=lg.INFO)


def extract_text_from_pdf(url):
    response = requests.get(url)

    if response.status_code != 200:
        return "Error"

    with open('temp.pdf', 'wb') as f:
        f.write(response.content)

    with pdfplumber.open('temp.pdf') as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    
    os.remove("temp.pdf")

    return text

def create_webdriver(driver_path=None, active_options=False):
    if active_options:
        options = Options()
        options.add_argument('--headless')
    else:
        options = Options()
    
    if driver_path is not None:
        path_driver = driver_path
    else:
        path_driver = 'chromedriver'
    service = Service()
    

    pager = webdriver.Chrome(service=service, options=options)
    return pager


def scroll(pager, speed=50, last_pos=0):
    last_height = pager.execute_script("return document.body.scrollHeight")
    for i in range(last_pos, last_height, speed):
        pager.execute_script(f"window.scrollTo({last_pos}, {i});")

    return last_height


def get_page_source(url, pager, scrolling=False, close=False, waiter=60):
    lg.info('Launching driver')
    pager.get(url)


    if scrolling:
        scroll(pager)

        elapsed_time = 0
        interval = 1
        start_time = time.time()
        last_pos=0
        while elapsed_time < waiter:
            last_pos = scroll(pager, speed=50, last_pos=last_pos)
            last_pos -=200

            time.sleep(0.5)
            
            elapsed_time = time.time() - start_time
    page_source = pager.page_source
    
    if close:
        pager.close()
        lg.info('Closing driver')
    
    return page_source


def get_urls(url, page_source):
    soup = BeautifulSoup(page_source, 'lxml')
    url_root = url.split('/press')[0]
    contents = soup.find_all('dd')
    dates = soup.find_all("dt")

    d = {}
    index = 0
    for dt, ct in zip(dates, contents):
        all_lang = ct.find_all("a")[1:]
        for lang in all_lang:
            if 'href' not in lang.attrs:
                continue
            d[index] = {'language': lang['lang'] if 'lang' in lang.attrs else "en",
                        'url': url_root + lang["href"],
                        'date': dt.text}
            index += 1
    
    pd.DataFrame.from_dict(d, orient='index').to_csv('data/url.csv')

    return pd.DataFrame.from_dict(d, orient='index')


def choose(data, languages=None, years=None, drop=['2 August 2007',
                                                   '26 October 2014']):
    if languages is not None:
        data = data[data["language"].isin(languages)]
        data = data.reset_index(drop=True)

    if years is not None:
        data["year"] = pd.to_datetime(data["date"]).dt.year
        if len(years) == 2:
            data = data[data['year'].isin(range(years[0], years[1]))]
        elif len(years) == 1:
            data = data[data['year'].isin(range(years[0]))]
        data = data.reset_index(drop=True).drop(columns=["year"])

    if drop is not None:
        data = data[~data.date.isin(drop)]

    return data


def get_content_article(article):
    """
    Fonction pour extraire le texte d'un article donné.
    """
    content = []

    if article:
        for paragraph in article.find_all('p'):
            content.append(paragraph.text.strip())
    return ' '.join(content)


def extraire_texte_pdf_miner(lien):
        try:
            reponse = requests.get(lien)
            reponse.raise_for_status()

            fichier_pdf = BytesIO(reponse.content)
            texte = extract_text(fichier_pdf)
            return texte

        except requests.exceptions.RequestException as e:
            return f"Erreur lors du téléchargement du PDF : {e}"
        except Exception as e:
            return 'Error'
        

def scrap_content(links, pause=0, balise='main'):
    content = []
    for link in tqdm(links):
        #time.sleep(5)
        if link[-3:] == "pdf":
            content.append(extract_text_from_pdf(link))
            continue

        try:
            response = requests.get(link)
        except:
            content.append('Error')
            continue

        soup = BeautifulSoup(response.text, 'lxml')

        main_section = soup.find('main')
        
        if main_section:

            paragraphs = main_section.find_all('p')
            full_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            content.append(full_text)
        else:
            print(f"Pas de balise <main> trouvée sur {link}")
            content.append("Error")
            
        time.sleep(pause)
    
    return content



def export_to_csv(dataframe, file):
    try:
        dataframe.to_csv(f'data/{file}', index=False)
    except FileNotFoundError as e:
        lg.error(e)
    except:
        lg.error('Destination unknown')


def scrap_speechs(lang, years, file_name, write_csv=True, topic=False, waiter=10,
                  url = 'https://www.ecb.europa.eu/press/pubbydate/html/index.en.html',
                  from_url=""):
    if topic:
        url+= f"?topic={topic}"

    if from_url:
        data = pd.read_csv(from_url, orient='index')
    else:
        driver = create_webdriver(active_options=False)
        page_source = get_page_source(url, pager=driver, scrolling=True, waiter=waiter)
        data = get_urls(url, page_source)
    #data = choose(data, languages=lang, years=years) La fonction est a corriger (#TODO)
    articles = scrap_content(data.url)
    data["content"] = articles
    data.to_csv(f"./data/{file_name}")
    if write_csv:
        export_to_csv(data, file_name)
        lg.info(f'### {data.shape[0]} articles have been scraped ###')
