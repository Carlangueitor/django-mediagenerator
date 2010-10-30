from django.conf import settings
from mediagenerator.generators.bundles.base import Filter, FileFilter
from mediagenerator.utils import media_url
import logging
import posixpath
import re

url_re = re.compile(r'url\s*\(["\']?([\w\.][^:]*?)["\']?\)', re.UNICODE)

# Whether to rewrite CSS URLs, at all
REWRITE_CSS_URLS = getattr(settings, 'REWRITE_CSS_URLS', True)
# Whether to rewrite CSS URLs relative to the respective source file
# or whether to use "absolute" URL rewriting (i.e., relative URLs are
# considered absolute with regards to STATICFILES_URL)
REWRITE_CSS_URLS_RELATIVE_TO_SOURCE = getattr(settings,
    'REWRITE_CSS_URLS_RELATIVE_TO_SOURCE', True)

class URLRewriter(object):
    def __init__(self, base_path='./'):
        if not base_path:
            base_path = './'
        self.base_path = base_path

    def rewrite_urls(self, content):
        if not REWRITE_CSS_URLS:
            return content
        return url_re.sub(self.fixurls, content)

    def fixurls(self, match):
        url = match.group(1)
        hashid = ''
        if '#' in url:
            url, hashid = url.split('#', 1)
            hashid = '#' + hashid
        if ':' not in url and not url.startswith('/'):
            rebased_url = posixpath.join(self.base_path, url)
            rebased_url = posixpath.normpath(rebased_url)
            try:
                url = media_url(rebased_url, refresh=False)
            except:
                logging.error('URL not found: %s' % url)
        return 'url(%s%s)' % (url, hashid)

class CSSURL(Filter):
    """Rewrites URLs relative to media folder ("absolute" rewriting)."""
    def __init__(self, **kwargs):
        super(CSSURL, self).__init__(**kwargs)
        assert self.filetype == 'css', (
            'CSSURL only supports CSS output. '
            'The parent filter expects "%s".' % self.filetype)

    def get_output(self, variation):
        rewriter = URLRewriter()
        for input in self.get_input(variation):
            yield rewriter.rewrite_urls(input)

    def get_dev_output(self, name, variation):
        rewriter = URLRewriter()
        content = super(CSSURL, self).get_dev_output(name, variation)
        return rewriter.rewrite_urls(content)

class CSSURLFileFilter(FileFilter):
    """Rewrites URLs relative to input file's location."""
    def get_dev_output(self, name, variation):
        content = super(CSSURLFileFilter, self).get_dev_output(name, variation)
        if not REWRITE_CSS_URLS_RELATIVE_TO_SOURCE:
            return content
        rewriter = URLRewriter(posixpath.dirname(name))
        return rewriter.rewrite_urls(content)
