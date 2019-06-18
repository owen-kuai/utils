#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


lock = threading.Lock()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class FileWatcher(FileSystemEventHandler):

    def on_moved(self, event):

        super(FileWatcher, self).on_moved(event)
        now_time = time.strftime("[\033[32m INFO \033[0m]\033[34m %H:%M:%S \033[0m", time.localtime())
        what = 'directory' if event.is_directory else 'file'
        print("\033[31m{}\033".format(
            ' [0m{0} {1} Moved : from {2} to {3} '.format(now_time, what, event.src_path, event.dest_path)))

    def on_deleted(self, event):
        super(FileWatcher, self).on_deleted(event)
        now_time = time.strftime("[\033[32m INFO \033[0m]\033[34m %H:%M:%S \033[0m", time.localtime())
        what = 'directory' if event.is_directory else 'file'
        print("\033[31m{}\033".format('{0} {1} Deleted : {2} '.format(now_time, what, event.src_path)))

    def on_modified(self, event):
        print('#$@$#$#$@$$', event.src_path)
        super(FileWatcher, self).on_modified(event)
        now_time = time.strftime("[\033[32m INFO \033[0m]\033[34m %H:%M:%S \033[0m", time.localtime())
        what = 'directory' if event.is_directory else 'file'
        print("\033[31m{}\033".format('{0} {1} Modified : {2} '.format(now_time, what, event.src_path)))

    def on_created(self, event):
        super(FileWatcher, self).on_moved(event)
        now_time = time.strftime("[\033[32m INFO \033[0m]\033[34m %H:%M:%S \033[0m", time.localtime())
        what = 'directory' if event.is_directory else 'file'
        print("\033[31m{}\033".format('{0} {1} Created : {2} '.format(now_time, what, event.src_path)))


if __name__ == '__main__':
    path = SCRIPT_DIR if SCRIPT_DIR else '.'
    event_handler = FileWatcher()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
