from datetime import date, timedelta
from pathlib import Path
from typing import List
import gzip
import json
import http

from cachetools import cached, LRUCache
import tornado.options
import tornado.web


class ArchivesHandler(tornado.web.RequestHandler):

    def initialize(self):
        """Simple JSON API handler that returns JSON generated by the given callable"""
        self.archives_dir: Path = tornado.options.options.archives_dir

    async def get(self):
        """GET /_monitor/archives.json"""
        since = self._start_date()
        apaths = self._archive_paths_since(since)
        self.write({'reports': [self._load_archive(apath) for apath in apaths]})

    def _start_date(self) -> str:
        try:
            dt = self.get_query_argument('start', (date.today() - timedelta(days=7)).isoformat())
            date.fromisoformat(dt)
            return dt
        except ValueError:
            raise tornado.web.HTTPError(http.HTTPStatus.BAD_REQUEST, 'start parameter must be ISO date')

    def _archive_paths_since(self, since: str) -> List[Path]:
        condition = lambda p: p.name > since and '_chat' not in p.name and p.name.endswith('.json.gz')
        return list(sorted(filter(condition, self.archives_dir.iterdir())))

    @cached(LRUCache(50))
    def _load_archive(self, apath: Path) -> dict:
        with gzip.open(apath, 'rt') as gfile:
            return json.load(gfile)
