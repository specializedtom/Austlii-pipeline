import unittest

from src.ingest.austlii.discover import discover_legislation_urls
from src.models.legislation import Jurisdiction


class _StubClient:
    def fetch(self, _url):
        return """
        <html><body>
          <a href='aaa2024/'>AAA Act 2024</a>
          <a href='/au/legis/cth/consol_act/bbb2020/'>BBB Act 2020</a>
          <a href='https://example.com/not-austlii'>skip</a>
        </body></html>
        """


class DiscoverTests(unittest.TestCase):
    def test_discover_legislation_urls_filters_and_limits(self):
        urls = discover_legislation_urls(Jurisdiction.CTH, client=_StubClient(), max_docs=2)
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("/cth/consol_act/" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
