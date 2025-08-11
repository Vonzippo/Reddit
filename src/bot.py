#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from dotenv import load_dotenv
load_dotenv()

from bots.reddit import RedditBot
from utils import countdown
from logs.logger import log

def run():
  reddit = RedditBot()
  while True:
    reddit.run()
    countdown(1)
