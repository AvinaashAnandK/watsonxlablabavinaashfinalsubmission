import streamlit as st
from exa_py import Exa
import os
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import datetime
import re
import unicodedata
from ibm_watsonx_ai.foundation_models import Model
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import cohere
import numpy as np
import pandas as pd
import io

st.set_page_config(page_title="CompanyMatch - Find Similar Companies in Other Geographies", layout="wide")

# Load environment variables
load_dotenv()

# API Keys
EXA_API_KEY = os.getenv('EXA_API_KEY')
WATSONX_API_KEY = os.getenv('WATSON_X_KEY')
WATSON_X_SPACE_ID = os.getenv('WATSON_X_SPACE_ID')
WATSON_X_PROJECT_ID = os.getenv('WATSON_X_PROJECT_ID')
WATSON_X_ENDPOINT = os.getenv('WATSON_X_ENDPOINT')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')

exa = Exa(api_key=EXA_API_KEY)
co = cohere.Client(api_key=COHERE_API_KEY)

company_structured_info_mapper = {
    "name":"Company Name",
    "industry": "Industry",
    "subindustry": "Sub-Industry",
    "market_position": "Market Position",
    "product_service_offerings": "Product / Service Offerings",
    "strategy": "Strategy",
    "other_information": "Other Information",
}

countries_list = ['Algeria', 'Argentina', 'Australia', 'Austria', 'Bangladesh', 'Belgium', 'Bolivia', 'Brazil', 'Canada', 'Chile', 'China', 'Colombia', 'Denmark', 'Dominican Republic', 'Egypt', 'Ethiopia', 'Finland', 'France', 'Germany', 'Hong Kong', 'India', 'Indonesia', 'Ireland', 'Israel', 'Italy', 'Japan', 'Kenya', 'Kenya', 'Malaysia', 'Mexico', 'Morocco', 'Netherlands', 'New Zealand', 'Nigeria', 'Pakistan', 'Paraguay', 'Peru', 'Philippines', 'Qatar', 'Saudi Arabia', 'Singapore', 'South Africa', 'South Korea', 'Spain', 'Sri Lanka', 'Sweden', 'Switzerland', 'Taiwan', 'Tanzania', 'Thailand', 'Turkey', 'UK', 'USA', 'United Arab Emirates', 'Uruguay', 'Vietnam']

domain_name_mapper = { '36kr.com': '36Kr', 'aa.com.tr': 'Anadolu Agency', 'aastocks.com': 'AASTOCKS', 'abc.net.au': 'ABC News (Australia)', 'addisfortune.news': 'Addis Fortune', 'affarsworld.se': 'Affärsvärlden', 'afr.com': 'Australian Financial Review', 'al-jazirah.com': 'Al Jazirah', 'aleqt.com': 'Aleqtisadiah', 'ambito.com': 'Ámbito', 'americaeconomia.com': 'América Economía', 'amwalalghad.com': 'Amwal Al Ghad', 'arabianbusiness.com': 'Arabian Business', 'argaam.com': 'Argaam', 'axios.com': 'Axios', 'bangkokpost.com': 'Bangkok Post', 'barrons.com': 'Barron\'s', 'berlingske.dk': 'Berlingske', 'bfmtv.com': 'BFMTV', 'bisnis.com': 'Bisnis Indonesia', 'bloomberg.com': 'Bloomberg', 'bloomberglinea.com': 'Bloomberg Línea', 'bnamericas.com': 'BNamericas', 'bnnbloomberg.ca': 'BNN Bloomberg', 'borsaitaliana.it': 'Borsa Italiana', 'borsen.dk': 'Børsen', 'breakit.se': 'Breakit', 'brecorder.com': 'Business Recorder', 'bridge.jp': 'Bridge', 'business-standard.com': 'Business Standard', 'business.dk': 'Berlingske Business', 'businessdailyafrica.com': 'Business Daily Africa', 'businessday.ng': 'BusinessDay', 'businessinsider.com': 'Business Insider', 'businesslive.co.za': 'Business Live', 'businessnews.com.au': 'Business News Australia', 'businesspost.ie': 'Business Post', 'businesstimes.com.sg': 'The Business Times', 'businesstoday.in': 'Business Today', 'businessworld.com.ph': 'BusinessWorld', 'caixin.com': 'Caixin Global', 'calcalist.co.il': 'Calcalist', 'capital.com.et': 'Capital Ethiopia', 'capital.de': 'Capital', 'challenge.ma': 'Challenge', 'challenges.fr': 'Challenges', 'chosun.com': 'The Chosun Ilbo', 'cityam.com': 'City A.M.', 'cnbc.com': 'CNBC', 'corriere.it': 'Corriere della Sera', 'cronista.com': 'El Cronista', 'crunchbase.com': 'Crunchbase', 'dailymirror.lk': 'Daily Mirror (Sri Lanka)', 'dailynewsegypt.com': 'Daily News Egypt', 'dailysabah.com': 'Daily Sabah', 'dailysocial.id': 'DailySocial', 'dawn.com': 'Dawn', 'derstandard.at': 'Der Standard', 'df.cl': 'Diario Financiero', 'di.se': 'Dagens Industri', 'diepresse.com': 'Die Presse', 'digitalnewsasia.com': 'Digital News Asia', 'digitimes.com': 'DigiTimes', 'dinero.com': 'Dinero', 'e.vnexpress.net': 'VnExpress', 'economictimes.indiatimes.com': 'The Economic Times', 'eleconomista.com.mx': 'El Economista', 'elfinanciero.com.mx': 'El Financiero', 'elmoudjahid.com': 'El Moudjahid', 'en.globes.co.il': 'Globes (English)', 'enterprise.press': 'Enterprise', 'entrackr.com': 'Entrackr', 'exame.com': 'Exame', 'expansion.mx': 'Expansión', 'fastcompany.com': 'Fast Company', 'fd.nl': 'Het Financieele Dagblad', 'fin24.com': 'Fin24', 'financialexpress.com': 'The Financial Express', 'financialpost.com': 'Financial Post', 'finans.dk': 'Finans', 'finews.ch': 'finews.ch', 'forbes.com': 'Forbes', 'fortune.com': 'Fortune', 'ft.com': 'Financial Times', 'ft.lk': 'Financial Times (Sri Lanka)', 'gestion.pe': 'Gestión', 'globes.co.il': 'Globes', 'gruenderszene.de': 'Gründerszene', 'gulf-times.com': 'Gulf Times', 'gulfnews.com': 'Gulf News', 'haaretz.com': 'Haaretz', 'handelsblatt.com': 'Handelsblatt', 'handelszeitung.ch': 'Handelszeitung', 'hankyung.com': 'The Korea Economic Daily', 'hkej.com': 'Hong Kong Economic Journal', 'hket.com': 'Hong Kong Economic Times', 'hurriyetdailynews.com': 'Hürriyet Daily News', 'idealog.co.nz': 'Idealog', 'ilsole24ore.com': 'Il Sole 24 Ore', 'inc42.com': 'Inc42', 'independent.ie': 'Irish Independent', 'interest.co.nz': 'Interest.co.nz', 'iprofesional.com': 'iProfesional', 'irishtimes.com': 'The Irish Times', 'japantimes.co.jp': 'The Japan Times', 'jpost.com': 'The Jerusalem Post', 'kauppalehti.fi': 'Kauppalehti', 'ked.co.kr': 'Korea Economic Daily', 'khaleejtimes.com': 'Khaleej Times', 'kontan.co.id': 'Kontan', 'koreaherald.com': 'The Korea Herald', 'larepublica.co': 'La República (Colombia)', 'latamlist.com': 'LatamList', 'latribune.fr': 'La Tribune', 'lecho.be': 'L\'Echo', 'leconews.com': 'L\'Economiste', 'lefigaro.fr': 'Le Figaro', 'lesechos.fr': 'Les Echos', 'leseco.ma': 'L\'Economiste (Morocco)', 'livemint.com': 'Mint', 'lta.reuters.com': 'Reuters Latin America', 'manager-magazin.de': 'Manager Magazin', 'marketwatch.com': 'MarketWatch', 'mb.com.ph': 'Manila Bulletin', 'medias24.com': 'Medias24', 'milanofinanza.it': 'Milano Finanza', 'mk.co.kr': 'Maeil Business Newspaper', 'moneycontrol.com': 'Moneycontrol', 'moneyweb.co.za': 'Moneyweb', 'mt.co.kr': 'Money Today', 'nairametrics.com': 'Nairametrics', 'nation.africa': 'Nation Africa', 'nationthailand.com': 'The Nation Thailand', 'nbr.co.nz': 'The National Business Review', 'news.com.au': 'News.com.au', 'newspicks.com': 'NewsPicks', 'nikkei.com': 'Nikkei Asia', 'nos.nl': 'NOS', 'nu.nl': 'NU.nl', 'nytimes.com': 'The New York Times', 'nzherald.co.nz': 'The New Zealand Herald', 'nzz.ch': 'Neue Zürcher Zeitung', 'portafolio.co': 'Portafolio', 'pulso.cl': 'Pulso', 'repubblica.it': 'La Repubblica', 'reuters.com': 'Reuters', 'rte.ie': 'RTÉ', 'rtlnieuws.nl': 'RTL Nieuws', 'scmp.com': 'South China Morning Post', 'scoop.co.nz': 'Scoop', 'semanaeconomica.com': 'Semana Económica', 'sina.com.cn': 'Sina', 'smartcompany.com.au': 'SmartCompany', 'smh.com.au': 'The Sydney Morning Herald', 'standard.co.uk': 'Evening Standard', 'standardmedia.co.ke': 'The Standard', 'startse.com': 'StartSe', 'startupdaily.net': 'Startup Daily', 'straitstimes.com': 'The Straits Times', 'stuff.co.nz': 'Stuff', 'taipeitimes.com': 'Taipei Times', 'talouselama.fi': 'Talouselämä', 'tbsnews.net': 'TBS News', 'techcrunch.com': 'TechCrunch', 'techforkorea.com': 'Tech for Korea', 'techinasia.com': 'Tech in Asia', 'technews.tw': 'TechNews', 'telegraph.co.uk': 'The Telegraph', 'theaustralian.com.au': 'The Australian', 'thedailystar.net': 'The Daily Star', 'theedgemarkets.com': 'The Edge Markets', 'theglobeandmail.com': 'The Globe and Mail', 'thenationalnews.com': 'The National', 'thepeninsulaqatar.com': 'The Peninsula', 'thestar.com.my': 'The Star', 'thisismoney.co.uk': 'This is Money', 'tijd.be': 'De Tijd', 'timesofisrael.com': 'The Times of Israel', 'tivi.fi': 'Tivi', 'toyokeizai.net': 'Toyo Keizai', 'trend.at': 'Trend', 'trends.be': 'Trends', 'tsena.com': 'Tsena', 'va.se': 'Veckans Affärer', 'valoreconomico.com.br': 'Valor Econômico', 'vanguardngr.com': 'Vanguard', 'vccircle.com': 'VCCircle', 'venturebeat.com': 'VentureBeat', 'vir.com.vn': 'Vietnam Investment Review', 'vnexpress.net': 'VnExpress', 'wiwo.de': 'WirtschaftsWoche', 'wsj.com': 'The Wall Street Journal', 'yicai.com': 'Yicai Global', 'yle.fi': 'Yle', 'yourstory.com': 'YourStory', 'zawya.com': 'Zawya' }

country_to_domain_mapper = {'Algeria': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Argentina': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Australia': ['stuff.co.nz', 'nzherald.co.nz', 'nbr.co.nz', 'interest.co.nz', 'scoop.co.nz', 'idealog.co.nz', 'afr.com', 'smh.com.au', 'theaustralian.com.au', 'abc.net.au', 'news.com.au', 'businessnews.com.au', 'startupdaily.net', 'smartcompany.com.au'], 'Austria': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Bangladesh': ['economictimes.indiatimes.com', 'livemint.com', 'business-standard.com', 'financialexpress.com', 'moneycontrol.com', 'yourstory.com', 'inc42.com', 'vccircle.com', 'entrackr.com', 'businesstoday.in', 'tbsnews.net', 'thedailystar.net', 'dawn.com', 'brecorder.com', 'dailymirror.lk', 'ft.lk'], 'Belgium': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Bolivia': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Brazil': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Canada': ['wsj.com', 'bloomberg.com', 'cnbc.com', 'forbes.com', 'businessinsider.com', 'fortune.com', 'fastcompany.com', 'techcrunch.com', 'nytimes.com', 'reuters.com', 'marketwatch.com', 'barrons.com', 'axios.com', 'venturebeat.com', 'crunchbase.com', 'financialpost.com', 'theglobeandmail.com', 'bnnbloomberg.ca'], 'Chile': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'China': ['hankyung.com', 'mk.co.kr', 'mt.co.kr', 'techforkorea.com', 'ked.co.kr', 'koreaherald.com', 'chosun.com', 'nikkei.com', 'japantimes.co.jp', 'bridge.jp', 'newspicks.com', 'toyokeizai.net', 'caixin.com', 'yicai.com', '36kr.com', 'scmp.com', 'sina.com.cn', 'technews.tw', 'digitimes.com', 'taipeitimes.com', 'hkej.com', 'aastocks.com', 'hket.com'], 'Colombia': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Denmark': ['di.se', 'va.se', 'breakit.se', 'affarsworld.se', 'borsen.dk', 'finans.dk', 'business.dk', 'berlingske.dk', 'kauppalehti.fi', 'tivi.fi', 'talouselama.fi', 'yle.fi'], 'Dominican Republic': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Egypt': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Ethiopia': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Finland': ['di.se', 'va.se', 'breakit.se', 'affarsworld.se', 'borsen.dk', 'finans.dk', 'business.dk', 'berlingske.dk', 'kauppalehti.fi', 'tivi.fi', 'talouselama.fi', 'yle.fi'], 'France': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Germany': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Hong Kong': ['hankyung.com', 'mk.co.kr', 'mt.co.kr', 'techforkorea.com', 'ked.co.kr', 'koreaherald.com', 'chosun.com', 'nikkei.com', 'japantimes.co.jp', 'bridge.jp', 'newspicks.com', 'toyokeizai.net', 'caixin.com', 'yicai.com', '36kr.com', 'scmp.com', 'sina.com.cn', 'technews.tw', 'digitimes.com', 'taipeitimes.com', 'hkej.com', 'aastocks.com', 'hket.com'], 'India': ['economictimes.indiatimes.com', 'livemint.com', 'business-standard.com', 'financialexpress.com', 'moneycontrol.com', 'yourstory.com', 'inc42.com', 'vccircle.com', 'entrackr.com', 'businesstoday.in', 'tbsnews.net', 'thedailystar.net', 'dawn.com', 'brecorder.com', 'dailymirror.lk', 'ft.lk'], 'Indonesia': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph'], 'Ireland': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Israel': ['globes.co.il', 'jpost.com', 'calcalist.co.il', 'en.globes.co.il', 'timesofisrael.com', 'haaretz.com', 'thenationalnews.com', 'khaleejtimes.com', 'gulfnews.com', 'arabianbusiness.com', 'argaam.com', 'aleqt.com', 'zawya.com', 'al-jazirah.com', 'gulf-times.com', 'thepeninsulaqatar.com', 'dailysabah.com', 'hurriyetdailynews.com', 'aa.com.tr'], 'Italy': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Japan': ['hankyung.com', 'mk.co.kr', 'mt.co.kr', 'techforkorea.com', 'ked.co.kr', 'koreaherald.com', 'chosun.com', 'nikkei.com', 'japantimes.co.jp', 'bridge.jp', 'newspicks.com', 'toyokeizai.net', 'caixin.com', 'yicai.com', '36kr.com', 'scmp.com', 'sina.com.cn', 'technews.tw', 'digitimes.com', 'taipeitimes.com', 'hkej.com', 'aastocks.com', 'hket.com'], 'Kenya': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Malaysia': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph'], 'Mexico': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Morocco': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Netherlands': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'New Zealand': ['stuff.co.nz', 'nzherald.co.nz', 'nbr.co.nz', 'interest.co.nz', 'scoop.co.nz', 'idealog.co.nz', 'afr.com', 'smh.com.au', 'theaustralian.com.au', 'abc.net.au', 'news.com.au', 'businessnews.com.au', 'startupdaily.net', 'smartcompany.com.au'], 'Nigeria': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Pakistan': ['economictimes.indiatimes.com', 'livemint.com', 'business-standard.com', 'financialexpress.com', 'moneycontrol.com', 'yourstory.com', 'inc42.com', 'vccircle.com', 'entrackr.com', 'businesstoday.in', 'tbsnews.net', 'thedailystar.net', 'dawn.com', 'brecorder.com', 'dailymirror.lk', 'ft.lk'], 'Paraguay': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Peru': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Philippines': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph'], 'Qatar': ['globes.co.il', 'jpost.com', 'calcalist.co.il', 'en.globes.co.il', 'timesofisrael.com', 'haaretz.com', 'thenationalnews.com', 'khaleejtimes.com', 'gulfnews.com', 'arabianbusiness.com', 'argaam.com', 'aleqt.com', 'zawya.com', 'al-jazirah.com', 'gulf-times.com', 'thepeninsulaqatar.com', 'dailysabah.com', 'hurriyetdailynews.com', 'aa.com.tr'], 'Saudi Arabia': ['globes.co.il', 'jpost.com', 'calcalist.co.il', 'en.globes.co.il', 'timesofisrael.com', 'haaretz.com', 'thenationalnews.com', 'khaleejtimes.com', 'gulfnews.com', 'arabianbusiness.com', 'argaam.com', 'aleqt.com', 'zawya.com', 'al-jazirah.com', 'gulf-times.com', 'thepeninsulaqatar.com', 'dailysabah.com', 'hurriyetdailynews.com', 'aa.com.tr'], 'Singapore': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph'], 'South Africa': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'South Korea': ['hankyung.com', 'mk.co.kr', 'mt.co.kr', 'techforkorea.com', 'ked.co.kr', 'koreaherald.com', 'chosun.com', 'nikkei.com', 'japantimes.co.jp', 'bridge.jp', 'newspicks.com', 'toyokeizai.net', 'caixin.com', 'yicai.com', '36kr.com', 'scmp.com', 'sina.com.cn', 'technews.tw', 'digitimes.com', 'taipeitimes.com', 'hkej.com', 'aastocks.com', 'hket.com'], 'Spain': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Sri Lanka': ['economictimes.indiatimes.com', 'livemint.com', 'business-standard.com', 'financialexpress.com', 'moneycontrol.com', 'yourstory.com', 'inc42.com', 'vccircle.com', 'entrackr.com', 'businesstoday.in', 'tbsnews.net', 'thedailystar.net', 'dawn.com', 'brecorder.com', 'dailymirror.lk', 'ft.lk'], 'Sweden': ['di.se', 'va.se', 'breakit.se', 'affarsworld.se', 'borsen.dk', 'finans.dk', 'business.dk', 'berlingske.dk', 'kauppalehti.fi', 'tivi.fi', 'talouselama.fi', 'yle.fi'], 'Switzerland': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'Taiwan': ['hankyung.com', 'mk.co.kr', 'mt.co.kr', 'techforkorea.com', 'ked.co.kr', 'koreaherald.com', 'chosun.com', 'nikkei.com', 'japantimes.co.jp', 'bridge.jp', 'newspicks.com', 'toyokeizai.net', 'caixin.com', 'yicai.com', '36kr.com', 'scmp.com', 'sina.com.cn', 'technews.tw', 'digitimes.com', 'taipeitimes.com', 'hkej.com', 'aastocks.com', 'hket.com'], 'Tanzania': ['businesslive.co.za', 'fin24.com', 'moneyweb.co.za', 'businessdailyafrica.com', 'nation.africa', 'standardmedia.co.ke', 'businessday.ng', 'nairametrics.com', 'vanguardngr.com', 'enterprise.press', 'amwalalghad.com', 'dailynewsegypt.com', 'elmoudjahid.com', 'leconews.com', 'tsena.com', 'addisfortune.news', 'capital.com.et', 'leseco.ma', 'challenge.ma', 'medias24.com'], 'Thailand': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph'], 'Turkey': ['globes.co.il', 'jpost.com', 'calcalist.co.il', 'en.globes.co.il', 'timesofisrael.com', 'haaretz.com', 'thenationalnews.com', 'khaleejtimes.com', 'gulfnews.com', 'arabianbusiness.com', 'argaam.com', 'aleqt.com', 'zawya.com', 'al-jazirah.com', 'gulf-times.com', 'thepeninsulaqatar.com', 'dailysabah.com', 'hurriyetdailynews.com', 'aa.com.tr'], 'UK': ['ft.com', 'telegraph.co.uk', 'thisismoney.co.uk', 'cityam.com', 'standard.co.uk', 'handelsblatt.com', 'manager-magazin.de', 'wiwo.de', 'capital.de', 'gruenderszene.de', 'diepresse.com', 'trend.at', 'derstandard.at', 'nzz.ch', 'handelszeitung.ch', 'finews.ch', 'lesechos.fr', 'latribune.fr', 'lefigaro.fr', 'challenges.fr', 'bfmtv.com', 'lecho.be', 'tijd.be', 'trends.be', 'fd.nl', 'nu.nl', 'rtlnieuws.nl', 'nos.nl', 'ilsole24ore.com', 'repubblica.it', 'corriere.it', 'milanofinanza.it', 'borsaitaliana.it', 'irishtimes.com', 'independent.ie', 'businesspost.ie', 'rte.ie', 'irishtimes.com'], 'USA': ['wsj.com', 'bloomberg.com', 'cnbc.com', 'forbes.com', 'businessinsider.com', 'fortune.com', 'fastcompany.com', 'techcrunch.com', 'nytimes.com', 'reuters.com', 'marketwatch.com', 'barrons.com', 'axios.com', 'venturebeat.com', 'crunchbase.com', 'financialpost.com', 'theglobeandmail.com', 'bnnbloomberg.ca'], 'United Arab Emirates': ['globes.co.il', 'jpost.com', 'calcalist.co.il', 'en.globes.co.il', 'timesofisrael.com', 'haaretz.com', 'thenationalnews.com', 'khaleejtimes.com', 'gulfnews.com', 'arabianbusiness.com', 'argaam.com', 'aleqt.com', 'zawya.com', 'al-jazirah.com', 'gulf-times.com', 'thepeninsulaqatar.com', 'dailysabah.com', 'hurriyetdailynews.com', 'aa.com.tr'], 'Uruguay': ['valoreconomico.com.br', 'exame.com', 'startse.com', 'elfinanciero.com.mx', 'expansion.mx', 'eleconomista.com.mx', 'cronista.com', 'iprofesional.com', 'ambito.com', 'portafolio.co', 'larepublica.co', 'dinero.com', 'df.cl', 'americaeconomia.com', 'pulso.cl', 'gestion.pe', 'semanaeconomica.com', 'latamlist.com', 'bnamericas.com', 'lta.reuters.com', 'bloomberglinea.com'], 'Vietnam': ['vnexpress.net', 'e.vnexpress.net', 'vir.com.vn', 'straitstimes.com', 'businesstimes.com.sg', 'techinasia.com', 'kontan.co.id', 'bisnis.com', 'dailysocial.id', 'thestar.com.my', 'theedgemarkets.com', 'digitalnewsasia.com', 'bangkokpost.com', 'nationthailand.com', 'businessworld.com.ph', 'mb.com.ph']}

def get_source_company_biz_model_info(company_name, geography, sources = None, results_count = 5):
    if sources:
        result = exa.search_and_contents(
            f"What does the company {company_name} in {geography} do? ",
            type="keyword",
            num_results=results_count,
            text=True,
            include_text=[company_name],
            summary={
                "query": f"Summarize {company_name}'s Products / Service Offerings, Customer Segment Focus, Revenue Model,  Distribution Channels and Business Model."
            },
            include_domains=sources
            )
        
        return result.results
    else:
        result = exa.search_and_contents(
            f"What does the company {company_name} in {geography} do? ",
            type="keyword",
            num_results=results_count,
            text=True,
            include_text=[company_name],
            summary={
                "query": f"Summarize {company_name}'s Products / Service Offerings, Customer Segment Focus, Revenue Model,  Distribution Channels and Business Model."
            }
            )
        return result.results

def get_comparable_companies_info(search_query, subindustry, geography, sources):
    result = exa.search_and_contents(
        search_query,
        type="neural",
        num_results=15,
        text=True,
        summary={
            "query": f"Only extract the top {subindustry} companies mentioned in the context which are based in or operate in {geography} along with a short description of the company. If no company is mentioned respond with \"No Companies\". "
        },
        include_domains=sources
        )
    
    return result.results

def get_urls(result_list):
    urls = []
    for search_result in result_list:
        urls.append(search_result.url)
    return urls

def get_content(result_list):
    text = []
    for search_result in result_list:
        text.append(search_result.text)
    return text

def get_citation(result_list):
    citation_list = []
    for article in result_list:
        title = article.title
        authors = article.author.split(', ') if article.author else []
        date_str = article.published_date
        url = article.url
        
        # Parse the date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_date = date_obj.strftime("%B %d, %Y")
            year = date_obj.year
        except ValueError:
            formatted_date = "No date"
            year = "n.d."
        
        # Format authors
        if len(authors) == 1:
            author_citation = authors[0]
        elif len(authors) == 2:
            author_citation = f"{authors[0]} & {authors[1]}"
        elif len(authors) > 2:
            author_citation = f"{authors[0]} et al."
        else:
            author_citation = ""
        
        # Extract website name from URL
        website_name = url.split('//')[1].split('/')[0].replace('www.', '')
        
        # Create the citation
        if author_citation:
            citation = f"{author_citation}. ({year}). {title}. {website_name}. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {url}"
        else:
            citation = f"{title}. ({year}). {website_name}. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {url}"

        citation_list.append(citation)

    return citation_list

def get_summaries(result_list):
    text = []
    for search_result in result_list:
        text.append(search_result.summary)
    return text

def get_summaries_with_dates(result_list):
    text = []
    for search_result in result_list:
        text.append(search_result.published_date)
        text.append(search_result.summary)
    return text

def get_content_and_title(result_list):
    text = []
    for search_result in result_list:
        text.append(search_result.title)
        text.append(search_result.text)
    return text

def clean_text(input, is_list=True):
    if is_list:
        text = ", ".join(str(item) for item in input if item is not None)
    else:
        text = str(input) if input is not None else ""

    text = re.sub(r'\s+', ' ', text)

    text = text.strip()

    text = ''.join(char for char in text if char.isprintable() or char.isspace())

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

    return text

def parse_company_xml(xml_string):
    try:
        # Try to parse the XML string
        root = ET.fromstring(xml_string)
    except ParseError as e:
        # If parsing fails, attempt to fix common issues
        print(f"Warning: XML parsing failed. Attempting to fix. Error: {e}")
        xml_string = xml_string.replace('&', '&amp;')  # Replace unescaped ampersands
        xml_string = f"<root>{xml_string}</root>"  # Wrap in root element if missing
        try:
            root = ET.fromstring(xml_string)
        except ParseError as e:
            print(f"Error: Failed to parse XML even after attempted fixes. Error: {e}")
            return "Error"

    # Dictionary to store the extracted information
    company_info = {}

    # List of expected tags
    expected_tags = ['name', 'industry','subindustry','market_position', 'product_service_offerings', 'strategy', 'other_information']

    # Extract information for each expected tag
    for tag in expected_tags:
        element = root.find(tag)
        if element is not None:
            company_info[tag] = element.text.strip() if element.text else ""
        else:
            print(f"Warning: Tag '{tag}' not found in the XML.")
            company_info[tag] = ""

    return company_info

def parse_flexible_xml(xml_string):
    # Dictionary to store the extracted information
    company_info = {}

    # Remove leading/trailing whitespace and newlines
    xml_string = xml_string.strip()

    # Remove the outer <company> tags if present
    xml_string = re.sub(r'^\s*<company>\s*|\s*</company>\s*$', '', xml_string, flags=re.DOTALL)

    # Regular expression to find tags and their content, allowing for whitespace and newlines
    pattern = r'<(\w+)>\s*(.*?)\s*</\w+>'

    # Find all matches in the XML string
    matches = re.findall(pattern, xml_string, re.DOTALL)

    # Process each match
    for tag, content in matches:
        # Strip whitespace and newlines from the content and join multiple lines
        cleaned_content = ' '.join(content.split())
        company_info[tag] = cleaned_content

    return company_info

def parse_search_terms(xml_string):
    try:
        # Try to parse the XML string
        root = ET.fromstring(xml_string)
    except ParseError as e:
        # If parsing fails, attempt to fix common issues
        print(f"Warning: XML parsing failed. Attempting to fix. Error: {e}")
        xml_string = xml_string.replace('&', '&amp;')  # Replace unescaped ampersands
        xml_string = f"<root>{xml_string}</root>"  # Wrap in root element if missing
        try:
            root = ET.fromstring(xml_string)
        except ParseError as e:
            print(f"Error: Failed to parse XML even after attempted fixes. Error: {e}")
            return None

    # List to store the extracted search terms
    search_terms = []

    # Extract all 'term' elements
    term_elements = root.findall('.//term')
    
    if not term_elements:
        print("Warning: No 'term' elements found in the XML.")
    
    # Extract text from each 'term' element
    for term in term_elements:
        if term.text:
            search_terms.append(term.text.strip())
        else:
            print("Warning: Empty term element found.")

    return search_terms

def parse_company_list(xml_string):
    # List to store company dictionaries
    companies = []

    # Remove leading/trailing whitespace and newlines
    xml_string = xml_string.strip()

    # Remove the outer <company_list> tags if present
    xml_string = re.sub(r'^\s*<company_list>\s*|\s*</company_list>\s*$', '', xml_string, flags=re.DOTALL)

    # Split the string into individual company blocks
    company_blocks = re.split(r'\s*</company>\s*', xml_string)

    # Process each company block
    for block in company_blocks:
        if block.strip():  # Check if the block is not empty
            company_info = {}
            
            # Regular expression to find tags and their content, allowing for whitespace and newlines
            pattern = r'<(\w+)>\s*(.*?)\s*</\1>'
            
            # Find all matches in the company block
            matches = re.findall(pattern, block, re.DOTALL)
            
            # Process each match
            for tag, content in matches:
                # Strip whitespace and newlines from the content and join multiple lines
                cleaned_content = ' '.join(content.split())
                company_info[tag] = cleaned_content
            
            if company_info:  # Only append if we found any information
                companies.append(company_info)

    return companies

def watsonx_company_information_summarizer(company_info):
    def get_credentials():
      return {
        "url" : WATSON_X_ENDPOINT,
        "apikey" : WATSONX_API_KEY
      }
    model_id = "ibm/granite-13b-chat-v2"
    parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 400,
    "repetition_penalty": 1
    }
    model = Model(
	model_id = model_id,
	params = parameters,
	credentials = get_credentials(),
	project_id = WATSON_X_PROJECT_ID,
	space_id = WATSON_X_SPACE_ID
	)

    prompt_input = f"""The following document is context on a company. Read the document and give me the output in XML format. Do not output anything apart from the XML text. 

Input: 2023-02-06T12:38:50.027Z, This page focuses on Beyond Meat\'s general information, including how to join their movement, not their products, service offerings, customer segment focus, revenue model, distribution channels, or business model. To find this information, you may need to visit other pages on the Beyond Meat website, or consult other sources. , 2024-01-01T00:00:00.000Z, Beyond Meat is a company that produces plant-based meat alternatives. Their products are designed to provide a "meaty" experience without the use of animal products. They market these products as "better-for-you" meals, implying health benefits and a more sustainable alternative. While specific details regarding their revenue model, customer segment focus, or distribution channels are not mentioned on the provided webpage, the page does link to a "Where to Buy" section which suggests a broad retail distribution model. , 2023-02-06T12:21:53.860Z, Beyond Meat is a Los Angeles-based company that produces plant-based meat substitutes. Founded in 2009, the company\'s initial products were launched in the United States in 2012. Their primary product offerings include plant-based chicken, beef, and pork alternatives. Beyond Meat targets customers interested in healthier, more sustainable, and ethical food choices. Their revenue model is based on selling their products through various distribution channels, including supermarkets, restaurants, and food retailers. Their business model emphasizes innovation, sustainability, and partnerships with key players in the food industry to expand their reach and market share. , 2023-02-06T20:40:49.283Z, Beyond Meat is a plant-based meat company whose mission is to provide a more sustainable alternative to traditional meat. Their product line includes plant-based burgers, sausages, ground meat, and other meat alternatives. They focus on consumers who desire a healthier, more environmentally friendly alternative to traditional meat products. Their revenue model is based on selling their products through a variety of distribution channels, including grocery stores, restaurants, and online retailers. Beyond Meats business model is centered on providing innovative, high-quality plant-based meat products that are both delicious and sustainable. , 2023-02-06T14:15:24.221Z, Beyond Meat offers plant-based burger patties, focusing on a customer segment seeking healthier, more sustainable meat alternatives. Their revenue model centers around selling these patties through various distribution channels including grocery stores, restaurants, and foodservice providers. While the webpage focuses primarily on their plant-based burger patties, it is not clear what their specific business model is, or if they offer any other products or services.
Output: <company>
    <name>Beyond Meat</name>
    <industry>Food and Beverage</industry>
    <subindustry>Plant-based Meat Alternatives</subindustry>
    <market_position>Beyond Meat is a Los Angeles-based company that produces plant-based meat alternatives, positioning itself as a leader in the sustainable food industry. Founded in 2009, they launched their first products in the United States in 2012.</market_position>
    <product_service_offerings>Their product line includes plant-based alternatives for chicken, beef, and pork, with specific offerings such as burger patties, sausages, and ground meat. These products are marketed as 'better-for-you' meals, emphasizing health benefits and sustainability.</product_service_offerings>
    <strategy>Beyond Meat's strategy focuses on innovation, sustainability, and partnerships with key players in the food industry. They target consumers interested in healthier, more sustainable, and ethical food choices. The company aims to expand its reach and market share by providing high-quality, plant-based meat products that are both delicious and environmentally friendly.</strategy>
    <other_information>Their revenue model is based on selling products through various distribution channels, including grocery stores, supermarkets, restaurants, food retailers, and online platforms. While specific details about their business model are not provided, it appears to center on developing and marketing innovative plant-based meat alternatives that appeal to health-conscious and environmentally aware consumers.</other_information>
  </company>

Input: 2023-02-27T03:47:44.742Z, Zalando is a leading European online platform for fashion and lifestyle, operating in 25 countries. They offer a wide selection of clothing and accessories from over 6,500 brands to their customers. Their business model is based on selling products directly to consumers through their online platform. They generate revenue through the sale of these products. Their distribution channel is exclusively online, operating through their website and mobile app. While details on their customer segment focus are not provided, their diverse offering suggests they target a wide range of customers with varied fashion needs. , 2023-02-06T09:12:17.803Z, Zalando is an online fashion and lifestyle platform based in Berlin, Germany. The company offers a wide variety of products, including clothing, shoes, accessories, and homeware, through its website and mobile app. Zalando targets a diverse customer segment of fashion-conscious individuals, catering to various ages, genders, and styles. The company\'s revenue model is based on commissions from third-party sellers, as well as direct sales of its own brands. Zalando\'s distribution channels include its own online platforms, as well as partnerships with other retailers and online marketplaces. The company\'s business model is centered on providing a seamless and personalized shopping experience for its customers. This includes offering fast and free shipping, flexible return policies, and a wide range of payment options. Zalando also invests heavily in technology and data analytics to personalize recommendations and optimize its customer journey. In Q3 2022, Zalando achieved significant growth with an active customer base surpassing 50 million. They are committed to sustainable practices and inclusivity, reflected in their initiatives like the "do.BETTER  Diversity & Inclusion Report 2022" and collaborations with other brands for climate action. , 2023-02-06T07:42:56.103Z, Zalando is an online fashion platform serving customers in 25 European markets. They offer a wide range of apparel, shoes, and accessories, focusing on delivering a convenient shopping experience with free delivery, 100-day return policy, and various local payment options. Zalando\'s business model centers on connecting fashion industry players, including customers, retailers, brands, stylists, factories, and advertisers. Their revenue is likely generated through commission fees from retailers, advertising revenue, and potentially direct sales of their own branded products. The company boasts a strong online presence and utilizes a network of 13 fulfillment centers across Europe for efficient distribution. Despite its large size, Zalando retains its start-up spirit, emphasizing testing and taking calculated risks to provide customers with unique and valuable experiences. , Zalando is an online retailer offering a wide selection of fashion, beauty, sportswear, designer items, and kids\' clothing. They provide free delivery and 100-day returns, allowing customers to browse and make purchases without pressure. The platform offers personalized product recommendations based on user preferences, and features a Zalando Plus membership program for enhanced benefits. Zalando focuses on customer convenience with features like size filters, brand following, and various payment options. They also offer transparency regarding product origins and certifications, appealing to environmentally conscious consumers. Zalando\'s revenue model is based on online sales of its products, with additional income likely generated through membership fees and potentially advertising partnerships. Their distribution channel is entirely online, with a website and mobile app facilitating the entire customer journey. , 2023-10-31T00:00:00.000Z, Zalando is an online fashion and lifestyle platform offering a range of products including shoes, apparel, accessories, and beauty products. Their core revenue comes from their "Fashion Store" segment which includes their main sales channels. Zalando also operates "Offspring", a segment that includes sales channels like Zelando Lounge, outlet stores, and overstock management. Finally, "All Other Segments" encompasses various emerging businesses. Zalando\'s business model relies on providing a curated online shopping experience for fashion-conscious customers. They achieve this through their various sales channels and by offering a wide variety of products.

Output: <company>
    <name>Zalando</name>
    <industry>Retail</industry>
    <subindustry>E-commerce Fashion and Lifestyle</subindustry>
    <market_position>Zalando is a leading European online platform for fashion and lifestyle, operating in 25 countries. They are one of the largest online fashion retailers in Europe, with over 50 million active customers as of Q3 2022.</market_position>
    <product_service_offerings>Zalando offers a wide range of products including clothing, shoes, accessories, beauty products, and homeware from over 6,500 brands. They also provide personalized shopping experiences, free delivery, 100-day returns, and various payment options. Additional services include the Zalando Plus membership program for enhanced benefits.</product_service_offerings>
    <strategy>Zalando's strategy focuses on providing a seamless and personalized shopping experience. They invest heavily in technology and data analytics for personalized recommendations and optimized customer journeys. The company emphasizes sustainability, inclusivity, and maintains a start-up spirit by encouraging testing and calculated risk-taking. Their business model connects various fashion industry players, including customers, retailers, brands, stylists, factories, and advertisers.</strategy>
    <other_information>Revenue is generated through multiple streams: commissions from third-party sellers, direct sales of their own brands, and potentially advertising partnerships and membership fees. Distribution is primarily online through their website and mobile app, supported by a network of 13 fulfillment centers across Europe. Zalando's business is structured into segments: 'Fashion Store' (main sales channels), 'Offspring' (including Zalando Lounge and outlet stores), and 'All Other Segments' (emerging businesses).</other_information>
  </company>

Input: {company_info}
Output:"""
    generated_response = model.generate_text(prompt=prompt_input, guardrails=True)

    return generated_response

def watsonx_search_term_generator(company_info):
    def get_credentials():
      return {
        "url" : "https://us-south.ml.cloud.ibm.com",
        "apikey" : WATSONX_API_KEY
      }
    model_id = "ibm/granite-13b-chat-v2"
    parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 400,
    "repetition_penalty": 1
    }
    model = Model(
	model_id = model_id,
	params = parameters,
	credentials = get_credentials(),
	project_id = WATSON_X_PROJECT_ID,
	space_id = WATSON_X_SPACE_ID
	)

    prompt_input = f"""The following document is context on a company. Read the document and give me the output in XML format. Do not output anything apart from the XML text. Make sure that only the target geography mentioned in the Input is included in the output. 

Input: I want to find comparable companies to the below company in India. \nName: Yeahka\nMarket Position: Yeahka is a Chinese payment-based technology platform that offers payment and business services to merchants and consumers in China.\nProduct / Service Offerings: Yeahka offers one-stop payment services, merchant solutions services, and in-store e-commerce services. These services enable merchants to accept non-cash payments from consumers, provide value-added services leveraging their customer base, and facilitate in-store e-commerce transactions.\nStrategy: Yeahka'\''s strategy focuses on providing comprehensive payment and business solutions to merchants and consumers in China. They aim to become a leading player in the mobile payment and retail technology industry in China.\nOther Information: Yeahka'\''s revenue comes from transaction fees on payments processed, subscriptions for software services, and interest income from lending activities. They distribute their services through online and offline channels, including their website, mobile app, and partnerships with merchants. Their business model is based on providing payment processing and value-added services to merchants and facilitating transactions between merchants and consumers.\n
Output: <search_terms>
<term>comparable companies to Yeahka in India payment services</term>
<term>payment technology companies in India</term>
<term>mobile payment solutions companies in India</term></search_terms>

Input: I want to find comparable companies to the below company in South Korea.\nCompany Name: MUJI\nMarket Position: MUJI is a Japanese retailer known for its minimalist and functional products, with a focus on simplicity, quality, and sustainability. They operate in over 1,000 stores worldwide and have an online presence through their website (muji.net and muji.com).\nProduct / Service Offerings: MUJI offers a wide range of products, including clothing, household goods, food, and even residential architectural design services. Their product range caters to a diverse customer segment, with over 7,000 items available in their stores.\nStrategy: MUJI'\''s strategy revolves around efficient production and distribution processes, a focus on functional designs, and a commitment to sustainability. They aim to create a positive impact on the environment and society through their minimalist approach and commitment to ethical production.\nOther Information: MUJI'\''s revenue model is based on direct sales through their online store and physical retail locations. They also generate revenue through licensing agreements and collaborations with other brands. Their distribution channels include a network of physical stores and their official website, with a focus on providing a seamless shopping experience for their customers.\n
Output: <search_terms>
<term>South Korean retailers with minimalist products</term>
<term>minimalist brands in South Korea</term>
<term>MUJI competitors South Korea</term>
<term>retailers similar to MUJI in South Korea</term>
</search_terms>

Input: {company_info}
Output:"""
    generated_response = model.generate_text(prompt=prompt_input, guardrails=True)

    return generated_response

def watsonx_comparables_shortlist(company_info):
    def get_credentials():
      return {
        "url" : "https://us-south.ml.cloud.ibm.com",
        "apikey" : WATSONX_API_KEY
      }
    model_id = "ibm/granite-13b-chat-v2"
    parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 400,
    "repetition_penalty": 1
    }
    model = Model(
	model_id = model_id,
	params = parameters,
	credentials = get_credentials(),
	project_id = WATSON_X_PROJECT_ID,
	space_id = WATSON_X_SPACE_ID
	)

    prompt_input = f"""The following document is context on a company. Read the document and give me the output in XML format. Do not output anything apart from the XML text. 

Input: I want the top 5 companies talked about in the following search summaries in the industry Technology and subindustry Artificial Intelligence. Give me the output in XML format. Do not output anything apart from the XML text.\nThe webpage lists top AI companies in France. The page highlights Edvantis and Yalantis as featured providers, but doesn't provide market share information. \nThe webpage lists 69 of 178 AI startups in France, collectively raising $7.2 billion in funding. Some key companies include: * **Mistral AI:** An AI-driven LLMs platform with $1.3 billion in Series A funding. * **BioSerenity:** An AI diagnostics platform with $90.5 million in Series B funding. * **Luko:** A neo-insurance company offering home insurance and security technology with $82.6 million in Series B funding. * **Meero:** A company offering AI-powered enhanced photography services with $230 million in Series C funding. Unfortunately, the webpage does not provide market share information for these companies. \nThis article lists 21 AI companies in France, but unfortunately doesn't provide market share data. Here are some of the key companies mentioned: * **Kili Technology:** A data-centric AI company that provides a labeling platform for high-quality training data. * **Berexia:** A Swiss company specializing in digital and IT engineering that helps international businesses manage risks through mathematical models. * **Pacte Novation:** An IT company specializing in software engineering that provides solutions for industries such as transportation and railways. * **SESAMm:** A leading artificial intelligence company serving investment firms and corporations globally. They analyze over 20 billion documents in real-time to generate insights for controversy detection, investment analysis, ESG, and positive impact scores. * **Prophesee:** A company developing event-based vision sensors that capture only changes in an image, making them more energy-efficient than traditional cameras. The article provides a brief overview of each company, including their website, headquarters, founding date, headcount, and latest funding type. \nThis webpage lists top AI companies in France, but it doesn't mention market share. However, it highlights companies like Akur8, specializing in AI-powered insurance pricing, Heex Technologies, focused on smart data management for autonomous driving, METRON, offering energy optimization for factories, Saagie, providing data platform for digital transformation, and SESAMm, specializing in AI-driven investment management using NLP. \nThe webpage lists top AI companies in France. The list is based on reviews, feedback and awards, with Kernix being the top-ranked company based on the information presented. Kernix is a development company founded in 2001, with a team of about 40 employees. It serves midmarket and small-business clients in education, business, and consumer products sectors. The webpage also mentions Managed Code, a mobile application development firm founded in 2021, and OrNsoft Corporation, a development firm headquartered in Miami with a satellite office in France, founded in 2006. While the list provides company descriptions, it does not contain information about market share for these companies.
Output: <company_list>
<company>
<name>Mistral AI</name>
<description>AI-driven LLMs platform</description>
<funding>$1.3 billion in Series A</funding>
</company>
<company>
<name>Meero</name>
<description>AI-powered enhanced photography services</description>
<funding>$230 million in Series C</funding>
</company>
<company>
<name>SESAMm</name>
<description>AI company for investment firms and corporations, analyzing documents for insights</description>
<funding>Not specified</funding>
</company>
<company>
<name>Kili Technology</name>
<description>Data-centric AI company providing labeling platform for training data</description>
<funding>Not specified</funding>
</company>
<company>
<name>Prophesee</name>
<description>Developing event-based vision sensors for energy-efficient image capture</description>
<funding>Not specified</funding>
</company>
</company_list>

Input: I want the top 5 companies talked about in the following search summaries in the industry Food Production and subindustry Ice Cream. Give me the output in XML format. Do not output anything apart from the XML text.\nThe list includes 13,596 Ice Cream Companies in Brazil. Sao Paulo has the largest market share with 3,799 companies (28%), followed by Belo Horizonte with 1,936 companies (14%) and Curitiba with 1,143 companies. These three cities combined have a 51% market share. The top 50 companies on the list include: MEIRELES FREITAS E ALMEIDA SERVICOS DE TELEATENDIMENTO Fortaleza, ALFAMA DISTRIBUIDORA DE PRODUTOS ALIMENTICIOS Curitiba, G G DA SILVA Vitoria, JAIR BRITO E FILHOS INDUSTRIA E COMERCIO DE GELO EIRELI Sao Goncalo, CAPIXABA DISTRIBUIDORA E LOGISTICA DE ALIMENTOS Serra, INDUSTRIA E COMERCIO DE PRODUTOS ALIMENTICIOS GELONI Guaraci, FABRICA DE GELO RAMIA E MARQUES EIRELI Marica, SORVETES SKIMIL & SKIMONI Americana, CONTRACT ENGENHARIA Fortaleza, SORVETES JUNDIA INDUSTRIA E COMERCIO Itupeva, Viper Servicos do Nordeste Fortaleza, MONDAY COMERCIO E DISTRIBUIDORA DE BEBIDAS Foz do Iguacu, INDUSTRIA ALIMENTICIA MONTE CLARO DE MERITI Sao Joao de Meriti, SUPERFRUT SORVETES Lages, Dihelo Alimentos Sao Miguel do Oeste, UDI UNIDADE DE DIAGNOSTICO INTEGRADO \nIn 2018, Nestle Brasil Ltda. had the highest brand penetration in Brazil's ice cream market, with over 21% of households purchasing their brand. Unilever Brasil Ltda., which markets Kibon and Ben & Jerry's, came in second with a 20.2% market share. Unfortunately, the specific market share data for other companies is behind a paywall and requires a Statista Premium Account. \nThis report provides data on the Brazil Take-Home and Bulk Ice Cream Market, but unfortunately, it doesn't explicitly mention specific companies or their market share. The report focuses primarily on market size, volume, and growth projections through 2026. It does provide breakdowns by different segments, like dairy-based vs. water-based ice cream, and distribution channels. If you're looking for company-specific information, you might need to consult other resources. \nChiquinho Ice Cream is a Brazilian ice cream company that has been in business since the 1980s. The company has a large network of franchises, and it is a popular choice for ice cream lovers in Brazil. While the article doesn't include information about market share, it does mention the company joining the franchising segment in 2010 with 80 shops. CHQ Companhia de Franchising was created to manage the Chiquinho Ice Cream brand and expand its business. \nThis article doesn't mention any specific ice cream companies or their market share. It focuses on popular ice cream flavors in Brazil, such as coconut, vanilla, plum, avocado, mango, papaya, acai, chocolate nut, rum raisin, tapioca, cheese, corn, peanut, cashew fruit, and many more. It also lists some unique Brazilian fruits that are often made into ice cream, like soursop, jabuticaba, mangaba, umbu, cupuacu, bacuri, tucuma, tapereba, fruta do conde, lychee, and pitanga."
Output: <company_list>
<company>
<name>Nestle Brasil Ltda.</name>
<description>Highest brand penetration in Brazil's ice cream market</description>
<funding>Over 21% of households purchasing their brand in 2018</funding>
</company>
<company>
<name>Unilever Brasil Ltda.</name>
<description>Markets Kibon and Ben & Jerry's ice cream brands</description>
<funding>20.2% market share in 2018</funding>
</company>
<company>
<name>Chiquinho Ice Cream</name>
<description>Popular ice cream company with a large franchise network</description>
<funding>80 shops in 2010 when joining the franchising segment</funding>
</company>
<company>
<name>SORVETES SKIMIL & SKIMONI</name>
<description>Ice cream company based in Americana</description>
<funding>Not specified</funding>
</company>
<company>
<name>SORVETES JUNDIA INDUSTRIA E COMERCIO</name>
<description>Ice cream company based in Itupeva</description>
<funding>Not specified</funding>
</company>
</company_list>

Input: {company_info}
Output:"""
    generated_response = model.generate_text(prompt=prompt_input, guardrails=True)

    return generated_response

def calculate_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text):
    res = co.embed(texts=[text],
                   model="embed-english-v3.0",
                   input_type="search_query",
                   embedding_types=['float'])
    return res.embeddings.float[0]

def compare_companies(source, comparable, fields):
    similarities = {}
    
    # Calculate field-specific similarities
    for field in fields:
        if field in source and field in comparable:
            source_embedding = get_embedding(source[field])
            comparable_embedding = get_embedding(comparable[field])
            similarities[field] = calculate_similarity(source_embedding, comparable_embedding) * 100
        else:
            similarities[field] = 0.0
    
    # Calculate aggregate similarity for specific fields
    aggregate_similarity = sum(similarities.values()) / len(similarities)
    similarities['aggregate'] = aggregate_similarity
    
    # Calculate overall similarity
    all_source_text = " ".join([source.get(field, "") for field in fields])
    all_comparable_text = " ".join([comparable.get(field, "") for field in fields])
    source_overall_embedding = get_embedding(all_source_text)
    comparable_overall_embedding = get_embedding(all_comparable_text)
    overall_similarity = calculate_similarity(source_overall_embedding, comparable_overall_embedding) * 100
    similarities['overall'] = overall_similarity
    
    return similarities

def get_company_structured_info(company,geography,sources=None):
    if sources:
        biz_model_info = get_source_company_biz_model_info(company, geography,sources)
    else:
        biz_model_info = get_source_company_biz_model_info(company, geography)

    biz_model_info_summary_raw = get_summaries(biz_model_info)
    biz_model_info_urls = get_citation(biz_model_info)
    biz_model_info_summary = clean_text(biz_model_info_summary_raw)
    source_company_summary = watsonx_company_information_summarizer(biz_model_info_summary)
    result = parse_company_xml(source_company_summary)
    if result == "Error":
        result = parse_flexible_xml(source_company_summary)
    
    return result, biz_model_info_urls
    
def get_search_terms_for_comparables(result, target_geography):
    search_term_generator_input = ""
    search_term_generator_input += f"I want to find comparable companies to the below company in {target_geography}. \n"
    for key in result.keys():
        search_term_generator_input += f"{company_structured_info_mapper[key]}: {result[key]} \n"
    
    search_term_generator_raw = watsonx_search_term_generator(search_term_generator_input)
    generated_search_terms = parse_search_terms(search_term_generator_raw)  
    return generated_search_terms

def get_comparables_shortlist(source_company_info, target_geography, sources):
    result_summaries = []
    # exa_results_raw = get_comparable_companies_info(generated_search_terms[1])

    subindustry = source_company_info['subindustry']
    search_query = f"List of {subindustry} companies in {target_geography}"

    exa_results_raw = get_comparable_companies_info(search_query,subindustry,target_geography,sources)
    comparables_citation = get_citation(exa_results_raw)
    exa_results_content = get_summaries(exa_results_raw)
    for result_raw in exa_results_content:
            if "No Companies" not in result_raw:
                result_summaries.append(clean_text(result_raw, is_list=False))    
    
    competitor_indentification_prompt = f"I want the top 5 companies talked about in the following search summaries in the industry {source_company_info['industry']} and subindustry {source_company_info['subindustry']}. Give me the output in XML format. Do not output anything apart from the XML text.\n"

    competitor_indentification_prompt += " \n".join(result_summaries[:5])

    comparables_raw = watsonx_comparables_shortlist(competitor_indentification_prompt)
    comparables_cleaned = parse_company_list(comparables_raw)

    if len(comparables_cleaned) > 3:
        top_3_comparables = comparables_cleaned[:3]
        others = comparables_cleaned[3:] 
    else:
        top_3_comparables = comparables_cleaned
        others = []
    
    return top_3_comparables, others, comparables_citation

def create_comparison_dataframe(source_company_info, comparables_company_info, source_comparable_similarities):
    # Create the base DataFrame with the source company info
    df = pd.DataFrame({
        'Field': [company_structured_info_mapper[key] for key in source_company_info.keys()],
        'Source': source_company_info.values()
    })
    
    # Add columns for each comparable company
    for i, comparable in enumerate(comparables_company_info, 1):
        column_name = f'Comparable #{i} ({comparable["name"]})'
        df[column_name] = [comparable.get(key, "N/A") for key in source_company_info.keys()]
    
    # Add similarity scores
    for i, similarities in enumerate(source_comparable_similarities, 1):
        column_name = f'Similarity #{i}'
        df[column_name] = [similarities.get(key, "N/A") for key in source_company_info.keys()]
        # Format similarity scores
        df[column_name] = df[column_name].apply(lambda x: f"{float(x):.1f}%" if x != "N/A" else "N/A")
    
    # Replace all remaining NaN values with "N/A"
    df = df.replace({np.nan: "N/A"})
    
    return df

def df_to_pdf(df, source_company='', target_geography=''):
    buffer = io.BytesIO()
    title = f'Identifying companies similar to {source_company} in {target_geography}'
    
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=0.3*inch)
    elements.append(Paragraph(title, title_style))

    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)

    data = [[Paragraph(str(cell), header_style) for cell in df.columns.tolist()]]
    for row in df.values:
        data.append([Paragraph(str(cell), cell_style) for cell in row])

    col_widths = [1.5*inch, 2.2*inch, 2.2*inch, 2.2*inch, 1*inch, 1*inch]

    t = Table(data, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    t.setStyle(style)

    elements.append(t)

    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


st.title("CompanyMatch - Find Similar Companies in Other Geographies")

if 'source_company' not in st.session_state:
    st.session_state.source_company = ""
if 'source_geography' not in st.session_state:
    st.session_state.source_geography = None
if 'target_geography' not in st.session_state:
    st.session_state.target_geography = None

# Function to check if all fields are filled
def are_fields_filled():
    return (st.session_state.source_company != "" and
            st.session_state.source_geography is not None and
            st.session_state.target_geography is not None)

# Input fields
source_company = st.text_input(
    "Source Company",
    placeholder="Enter company name here...",
    key="source_company"
)

source_geography = st.selectbox(
    "Where is it located?",
    countries_list,
    key="source_geography",
    index=None,
    placeholder="Select source geography..."
)

target_geography = st.selectbox(
    "Where do you want to find comparable companies in?",
    countries_list,
    key="target_geography",
    index=None,
    placeholder="Select target geography..."
)

st.info('Currently all public and private companies are looked at!', icon="ℹ️")
st.divider() 
if st.button("Search", disabled=not are_fields_filled()):
    source_geo_sources_domain = country_to_domain_mapper[st.session_state.source_geography]
    target_geo_sources_domain = country_to_domain_mapper[st.session_state.target_geography]
    
    source_geo_sources_names = []
    for dom in source_geo_sources_domain:
        source_geo_sources_names.append(domain_name_mapper[dom])
    
    target_geo_sources_names = []
    for dom in target_geo_sources_domain:
        target_geo_sources_names.append(domain_name_mapper[dom])

    with st.spinner("Fetching company information..."):
        if st.session_state.source_company != "" and st.session_state.source_geography is not None:
            st.caption(f"Looking for more information on {source_company} in the following sources:")
            st.markdown(
                        f"""
                        <div style='
                            background-color: #e64980;
                            color: white;
                            padding: 0.2rem 0.5rem;
                            border-radius: 0.5rem;
                            margin-bottom: 0.5rem;
                            font-size: 0.8em;
                            display: inline-block;
                        '>
                            {" , ".join(source_geo_sources_names)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        source_company_info, citation_source_company_info = get_company_structured_info(source_company, source_geography, source_geo_sources_domain)

    if source_company_info['name'] == "":
        st.error("No information found for the source company. Please try again.")
    else:
        st.subheader("Source Company Information")
        
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Company Name:** {source_company_info['name']}")
            st.markdown(f"**Industry:** {source_company_info['industry']}")
            st.markdown(f"**Subindustry:** {source_company_info['subindustry']}")
        
        with col2:
            st.markdown("**Market Position:**")
            st.info(source_company_info['market_position'])
        
        st.markdown("**Product/Service Offerings:**")
        st.info(source_company_info['product_service_offerings'])
        
        st.markdown("**Strategy:**")
        st.info(source_company_info['strategy'])
        
        if source_company_info.get('other_information'):
            st.markdown("**Other Information:**")
            st.info(source_company_info['other_information'])

        with st.spinner("Finding comparable companies..."):
            st.caption(f"Looking for more information on comparable companies in the following sources:")
            st.markdown(
                        f"""
                        <div style='
                            background-color: #9775fa;
                            color: white;
                            padding: 0.2rem 0.5rem;
                            border-radius: 0.5rem;
                            margin-bottom: 0.5rem;
                            font-size: 0.8em;
                            display: inline-block;
                        '>
                            {" , ".join(target_geo_sources_names)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            top3_companies, other_companies, citation_comparables = get_comparables_shortlist(source_company_info, target_geography,target_geo_sources_domain)

        comparable_companies_considered = "Diving deep on the following companies for the report: "
        deep_dive_cos = [co['name'] for co in top3_companies]
        comparable_companies_considered += ", ".join(deep_dive_cos)
        st.info(comparable_companies_considered)

        if len(other_companies) > 0:
            comparable_companies_not_considered = "The following companies are also comparable, but not included in this report: "
            list_of_comps = [other['name'] for other in other_companies]
            comparable_companies_not_considered += ", ".join(list_of_comps)
            st.info(comparable_companies_not_considered)

        comparables_company_info_raw = []
        citation_comparable_company_info_list = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("Fetching company level information on comparable companies..."):
            for i, company in enumerate(top3_companies):
                status_text.text(f"Processing company {i+1} of {len(top3_companies)}: {company['name']}")
                company_info, citation_comparable_company_info = get_company_structured_info(company['name'], target_geography)
                comparables_company_info_raw.append(company_info)
                citation_comparable_company_info_list.append(citation_comparable_company_info)
                progress_bar.progress((i + 1) / len(top3_companies))
        
        status_text.empty()

        comparables_company_info = [comp for comp in comparables_company_info_raw if comp.get('name', "")]

        fields = ['market_position', 'product_service_offerings', 'strategy', 'other_information']
        comparable_similarities = []
        for comp in comparables_company_info:
            comparable_similarities.append(compare_companies(source_company_info, comp, fields))

        df = create_comparison_dataframe(source_company_info, comparables_company_info, comparable_similarities)

        st.subheader("Comparison Table")
        st.dataframe(df)

        pdf_data = df_to_pdf(df, source_company, target_geography)
        
        if st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name="company_comparison.pdf",
            mime="application/pdf"
        ): 
            st.toast('Your PDF report was saved!', icon='🎉')
