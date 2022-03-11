[![Code Is Passing All Unit Tests?](https://github.com/1103s/crypto-bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/1103s/crypto-bot/actions/workflows/python-app.yml) [![Documentation Is Generated?](https://github.com/1103s/crypto-bot/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/1103s/crypto-bot/actions/workflows/gh-pages.yml) [![Publish To Docker](https://github.com/1103s/crypto-bot/actions/workflows/publish.yml/badge.svg)](https://github.com/1103s/crypto-bot/actions/workflows/publish.yml)

# Crypto Util

Real time cryptocurrency price data gathering and future price prediction command line utility using machine learning regression. Cross platform compatible on Linux, macOS, and Windows. 

## Install

### Docker or podman


- `docker pull yetanothercryptoutil/yacu` or

- `podman pull yetanothercryptoutil/yacu`


### Local installation
- Download and install anaconda
- git clone `https://github.com/1103s/crypto-bot.git`
- cd crpto-bot
- conda create --name crypto-util python=3.9.7
- source activate crypto-util
- python3 -m pip install -r requirements.txt

## Usage

### Local command line usage

- `python3 crypto_util.py --crypto BTC`: The basic functionality requires the user to input at least the cryptocurrency symbol. 
- `python3 crypto_uitl.py --crypto ETH --days 10 --lags 80`: More specific flags can be specified, such as the number of days into the future to predict the price.

### Docker or podman

- `docker run yacu` or
- `podman run yacu`

### Example Docker or podman Usage
- `podman run yacu --crypto ETH`: In this case the settings are set to default. However, the cryptocurrency you want to analyze is a required flag. 

- `podman run yacu --help` displays the usage and required arguments for the utility to work. 

## Documentation

Documentation can be found [here](https://1103s.github.io/crypto-bot/).

## Requirements

- docker, podman, or anaconda
