#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from nltk.corpus import stopwords
import locale


def vector(txt, path, keys):
    language, output_encoding = locale.getdefaultlocale()

    txt = txt.lower()
    bag = re.findall(u"[\w'áéíóúñ]+", txt, flags=re.UNICODE | re.LOCALE)
    e = [word for word in bag if
         word.encode('utf-8') not in stopwords.words('spanish') and
         word.encode('utf-8') not in stopwords.words('english') and
         word.encode('utf-8') not in stopwords.words('twitter') and
         word.encode('utf-8') not in keys and
         len(word.encode('utf-8')) > 2]

    return e
