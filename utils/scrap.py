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
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib3.connectionpool import log as urllibLogger


lg.basicConfig(level=lg.INFO)


def data_from_csv(csv_file):
    dataframe = pd.read_csv(csv_file)
    return dataframe


def specific_adjustment(data):
    mask = (data.date == '6 October 2011')
    obj = data.loc[mask, 'speech']
    obj = obj.map(lambda x: x.split('Rehn.')[1].strip())
    data.loc[mask, 'speech'] = obj.map(
        lambda x: x.split('Let me close')[0].strip())
    return data


def prune_head_tail(speech):
    speech = speech.strip().split('* * *')[0].strip()
    speech = speech.lower()
    speech = speech.strip().rsplit('. ', 1)[0].strip()
    try:
        speech = speech.split('s meeting.')[1].strip()
    except IndexError:
        try:
            speech = speech.split('commissioner almunia.')[1].strip()
        except IndexError:
            try:
                speech = speech.split('prime minister juncker.')[1].strip()
            except IndexError:
                pass
    return speech


def hasNumbers(string):
    return bool(re.search(r'\d', string))


def add_stopwords():
    sp = spacy.load("en_core_web_sm")
    spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
    add = ['ecb', 'basis', 'cet', 'utc', 'gmt', 'governing', 'council', 'let',
           'say', 'draghi', 'lagarde', 'trichet', 'mr', 'ms', 'papademos',
           'junker', 'euro', 'area', 'january', 'february', 'march', 'april',
           'june', 'july', 'august', 'september', 'october', 'november',
           'december', 'meeting', 'ii', 'iii', 'iv']
    spacy_stopwords.update(add)
    return spacy_stopwords


def preprocess_speech(speech):
    stopwords = add_stopwords()
    sp = spacy.load("en_core_web_sm")
    select = ' '.join(word.lemma_.lower() for word in sp(speech)
                      if not hasNumbers(str(word.lemma_))
                      if word.lemma_.lower() not in stopwords
                      and word.lemma_ not in ["-PRON-"]
                      and (len(word.text) > 1))
    return select


def select_ngrams(speechs, ngrams, min_df):
    ngrams = tuple(ngrams)
    tfidf_vectorizer = TfidfVectorizer(
        stop_words=None, ngram_range=ngrams, min_df=0.95)
    tfidf = tfidf_vectorizer.fit_transform(speechs)
    selected_ngrams = tfidf_vectorizer.get_feature_names()
    return selected_ngrams


def union_ngrams(*args):
    selected_ngrams = []
    for arg in args:
        selected_ngrams = list(set(selected_ngrams).union(set(arg)))
    return selected_ngrams


def add_ngrams(speech, selected_ngrams):
    for ngram in selected_ngrams:
        speech = re.sub(ngram.split()[0] + ' ' + ngram.split()[1],
                        ngram.split()[0] + '_' + ngram.split()[1], speech)
    return speech


def export_to_csv(dataframe, file):
    try:
        dataframe.to_csv(f'data/{file}', index=False)
    except FileNotFoundError as e:
        lg.error(e)
    except:
        lg.error('Destination unknown')


def process_speechs(inputs, output, ngrams, min_df, write_csv):
    dataframe = data_from_csv(os.path.join('data', inputs))
    dataframe = specific_adjustment(dataframe)
    dataframe.speech = dataframe.speech.map(lambda x: prune_head_tail(x))
    processed_speechs = dataframe.speech.map(lambda x: preprocess_speech(x))

    selected_ngrams = select_ngrams(
        processed_speechs, ngrams=ngrams, min_df=min_df)

    processed_speech = processed_speechs.map(
        lambda x: add_ngrams(x, selected_ngrams))
    dataframe['processed_speech'] = processed_speech

    if write_csv:
        export_to_csv(dataframe, output)

    lg.info(f'### Preprocessing is over, a file {output} has been created ###')


urllibLogger.setLevel(lg.WARNING)



def create_webdriver(driver_path=None, active_options=False):
    if active_options:
        options = Options()
        options.add_argument('--headless')  # Mode headless pour exécuter sans interface graphique
    else:
        options = Options()  # Options vides si non spécifiées
    
    if driver_path is not None:
        path_driver = driver_path
    else:
        path_driver = 'chromedriver'  # Utilise 'chromedriver' par défaut
    
    # Utilisation de la classe Service pour spécifier le chemin du ChromeDriver
    service = Service(executable_path=path_driver)
    
    # Création du WebDriver avec service et options
    pager = webdriver.Chrome(service=service, options=options)
    return pager


def scroll(pager, speed=50):
    last_height = pager.execute_script("return document.body.scrollHeight")
    for i in range(0, last_height, speed):
        pager.execute_script(f"window.scrollTo(0, {i});")
    pager.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def get_page_source(url, pager, scrolling=False, close=True):
    lg.info('Launching driver')
    pager.get(url)
    if scrolling:
        scroll(pager)
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
            d[index] = {'language': lang['lang'],
                        'url': url_root + lang["href"],
                        'date': dt.text}
            index += 1

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
    end = article.find(id='qa')
    article = BeautifulSoup(str(article).split(str(end))[0], 'lxml')
    all_paragraph = article.find_all('p')
    init = [article.find(class_='external'), article.find(class_='arrow')]
    content = ''
    start = False

    for p in all_paragraph:
        if (any([True for i in init if i in p])):
            try:
                all_paragraph.remove(p.find_next('p'))
            except AttributeError as AE:
                lg.warning(AE)
            start = True
            continue
        if start:
            content += p.text + ' '
    return content


def scrap_content(links, pause=0, balise='article'):
    content = []
    for link in links:
        soup = BeautifulSoup(requests.get(link).text, features='lxml')
        article = soup.select(balise)[0]
        content.append(get_content_article(article))
        time.sleep(pause)
    return content


def export_to_csv(dataframe, file):
    try:
        dataframe.to_csv(f'data/{file}', index=False)
    except FileNotFoundError as e:
        lg.error(e)
    except:
        lg.error('Destination unknown')


def scrap_speechs(lang, years, file_name, write_csv):
    url = 'https://www.ecb.europa.eu/press/pressconf/html/index.en.html'
    driver = create_webdriver(active_options=False)
    page_source = get_page_source(url, pager=driver, scrolling=True)
    data = get_urls(url, page_source)
    data = choose(data, languages=lang, years=years)
    articles = scrap_content(data.url)
    data["speech"] = articles

    if write_csv:
        export_to_csv(data, file_name)
        lg.info(f'### {data.shape[0]} speechs have been scraped ###')
