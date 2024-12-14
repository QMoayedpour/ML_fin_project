from setuptools import setup, find_packages

setup(
    name="ML_fin",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["numpy", "pandas", "tqdm", "matplotlib", "scikit-learn"],
    extras_require={
        'scrap': [
            'bs4',
            'spacy',
            'selenium',
            "pdfplumber",
            "pdfminer",
            "urllib3"

        ],
    },
)