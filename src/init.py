#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sys

# Avoid loading the heavy logger that loads reddit config
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    def error(self, msg):
        print(f"[ERROR] {msg}")

log = SimpleLogger()

import bot

if __name__ == "__main__":
    try:
        log.info('Starting December Content Bot (Using local data from december_top_content)')
        bot.run()
    except KeyboardInterrupt:
        log.info('Exiting December Content Bot')
        sys.exit()
    except Exception as e:
        log.error(f'Error: {e}')
        sys.exit(1)
