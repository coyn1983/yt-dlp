import re

from .common import InfoExtractor
from ..utils import clean_html, unified_strdate


class Cg51IE(InfoExtractor):
    IE_DESC = '51吃瓜网'
    _VALID_URL = r'https?://(?:www\.)?51cg1\.com/archives/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://51cg1.com/archives/277062/',
        'info_dict': {
            'id': '277062',
            'ext': 'mp4',
            'title': '抖音百万网红 刘大炮 出轨奶露拖 抛弃糟糠之妻 酒店开房视频被公之于众！',
            'age_limit': 18,
        },
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, headers={'Referer': 'https://51cg1.com/'})

        # DPlayer config lives in a single-quoted data-config attribute
        config = self._html_search_regex(
            r"data-config='([^']+)'", webpage, 'player config', default='')
        config = config.replace('\\/', '/')

        avc_url = self._search_regex(
            r'"video":\{"url":"([^"]+?\.m3u8[^"]*)"',
            config, 'hls url', default=None)
        h265_url = self._search_regex(
            r'"video_h265":\{"url":"([^"]+?\.m3u8[^"]*)"',
            config, 'h265 url', default=None)
        if not avc_url and not h265_url:
            self.raise_no_formats(
                'No video found (post may be image-only or requires login)',
                video_id=video_id)

        formats = []
        if avc_url:
            formats.extend(self._extract_m3u8_formats(
                avc_url, video_id, 'mp4', m3u8_id='hls'))
        if h265_url:
            for f in self._extract_m3u8_formats(
                    h265_url, video_id, 'mp4', m3u8_id='hls-h265'):
                f['vcodec'] = 'hevc'
                f['quality'] = -1  # prefer the avc stream for compatibility
                formats.append(f)

        title = (
            self._html_search_regex(
                r'<h1[^>]*>(.*?)</h1>', webpage, 'title', default=None)
            or self._html_search_regex(
                r'data-video_title="([^"]*)"', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or video_id)

        upload_date = unified_strdate(self._html_search_regex(
            r'itemprop="dateModified" content="([^"]+)"',
            webpage, 'upload date', default=None))

        return {
            'id': video_id,
            'title': clean_html(title).strip(),
            'formats': formats,
            'age_limit': 18,
            'upload_date': upload_date,
        }
