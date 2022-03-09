# crypto-bot
Apply machine learning to cryptocurrency data

# Code Health

[![Code Is Passing All Unit Tests?](https://github.com/1103s/crypto-bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/1103s/crypto-bot/actions/workflows/python-app.yml)

[![Documentation Is Generated?](https://github.com/1103s/crypto-bot/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/1103s/crypto-bot/actions/workflows/gh-pages.yml)

# Requirements
- python 3.9.1
- Anaconda
- pandas==1.4.0
- Install cryptoCMD (`https://github.com/guptarohit/cryptoCMD`) can be installed using `pip install git+git://github.com/guptarohit/cryptoCMD.git`
- scikit-learn==1.0.2
- numpy==1.22.2
- matplotlib==3.5.1
- yahoo-fin==0.8.9.1

# Data Sources
https://finance.yahoo.com
https://www.coingecko.com/en/coins/

# Coin ID reference in coin\_list.json

# Real-time data collection

# Historical BTC/USD, ETH/USD, LTC/USD
Go to https://www.cryptodatadownload.com/data/gemini/ and download the minute 
CSVs. Then move the CSV files into the data folder and run train\_model.py 
(doesn't yet exist)

