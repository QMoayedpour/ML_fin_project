import re
import string
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


def preprocess_text(text):
    text = text.lower()

    text = re.sub(f'[{string.punctuation}0-9]', ' ', text)

    words = word_tokenize(text)

    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words and len(word) > 1]

    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]

    return ' '.join(words)


def apply_tfidf(df):
    df['preprocessed_contents'] = df['content'].apply(preprocess_text)

    vectorizer = TfidfVectorizer()

    _ = vectorizer.fit_transform(df['preprocessed_contents'])

    idf_scores = vectorizer.idf_
    words = vectorizer.get_feature_names_out()

    idf_tuples = [(word, round(float(score), 3)) for word, score in zip(words, idf_scores)]

    idf_tuples_sorted = sorted(idf_tuples, key=lambda x: x[1], reverse=True)

    df['tfidf'] = [idf_tuples_sorted] * len(df)

    return df
