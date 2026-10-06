import re
from datetime import datetime, timezone

from .common import InfoExtractor
from ..utils import clean_html, unified_strdate


class JableIE(InfoExtractor):
    IE_DESC = 'JableTV'
    _VALID_URL = r'https?://(?:www\.)?jable\.tv/videos/(?P<id>[\w-]+)/?'
    _TESTS = [{
        'url': 'https://jable.tv/videos/ssis-406/',
        'info_dict': {
            'id': 'ssis-406',
            'ext': 'mp4',
            'title': 'startswith:SSIS-406',
            'age_limit': 18,
        },
        'params': {'skip_download': True},
    }]

    _REL_UNITS = {
        '年': ('days', 365),
        '個月': ('days', 30),
        '月': ('days', 30),
        '週': ('days', 7),
        '天': ('days', 1),
        '小時': ('seconds', 3600),
        '小時'.replace('小', '时'): ('seconds', 3600),
        '分鐘': ('seconds', 60),
        '分钟': ('seconds', 60),
    }

    def _relative_to_date(self, text):
        """Convert a relative Chinese timestamp like '4 年前' to an approx date."""
        m = re.search(r'(\d+)\s*(年|個月|月|週|天|小時|小时|分鐘|分钟)\s*前', text)
        if not m:
            return None
        value, unit = int(m.group(1)), self._REL_UNITS[m.group(2)]
        try:
            from datetime import timedelta
            return (datetime.now(timezone.utc) - timedelta(**{unit[0]: value * unit[1]})).strftime('%Y%m%d')
        except Exception:
            return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, impersonate=True,
            headers={'Referer': 'https://jable.tv/'})

        hls_url = self._search_regex(
            r'hlsUrl\s*=\s*(["\'])(?P<url>https?://.+?\.m3u8[^\1]*?)\1',
            webpage, 'm3u8 url', group='url')

        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(
                r'<h1[^>]+class="title"[^>]*>(.+?)</h1>',
                webpage, 'title', default=None)
            or self._html_search_regex(
                r'<h4[^>]*>(.+?)</h4>', webpage, 'title', default=None)
            or video_id)

        formats = self._extract_m3u8_formats(
            hls_url, video_id, 'mp4', m3u8_id='hls')

        # relative date ("4 年前") and view count follow the clock/eye icons
        rel_time = self._search_regex(
            r'#icon-clock[\s\S]{0,200}?<span[^>]*>([^<]+)</span>',
            webpage, 'relative date', default=None)
        views = self._search_regex(
            r'#icon-eye[\s\S]{0,200}?<span[^>]*>([\d\s,]+)</span>',
            webpage, 'view count', default=None)
        view_count = int(re.sub(r'[^\d]', '', views)) if views else None

        # actress links: <a class="model" href=".../models/<slug>/">...name in title attr or text...</a>
        cast = []
        for m in re.finditer(
                r'class="model"[^>]*href="[^"]*?/models/([\w-]+)/"[^>]*>(.*?)</a>',
                webpage, re.S):
            block = m.group(2)
            name = (
                self._search_regex(r'title="([^"]+)"', block, 'model name', default=None)
                or clean_html(re.sub(r'<[^>]+>', '', block)).strip())
            cast.append(name or m.group(1).replace('-', ' ').title())

        tags = re.findall(r'/categories/([\w%-]+)/', webpage)
        seen = set()
        tags = [t for t in tags if not (t in seen or seen.add(t))]

        return {
            'id': video_id,
            'title': clean_html(title),
            'formats': formats,
            'age_limit': 18,
            'upload_date': self._relative_to_date(rel_time or '') or unified_strdate(
                self._html_search_regex(
                    r'(\d{4}-\d{2}-\d{2})', webpage, 'date', default=None)),
            'view_count': view_count,
            'cast': cast or None,
            'tags': tags or None,
        }
