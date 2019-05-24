import os
import json
from unittest import TestCase

from infogetter import url_to_filename, InfoGetter, InvalidFilePath, BrokenJsonFile, BadUrlAtIPLookUp, NoApi, NoWhois, \
    NoGeo, NoSitemap


tests_urls = ['example.com', 'example.com/', 'example.com/asfaf/aa', 'www.example.com', 'www.example.com/',
              'www.example.com/asfjao/assa', 'http://www.example.com', 'http://www.example.com/',
              'http://www.example.com/asfagg', 'https://www.example.com', 'https://www.example.com/',
              'https://www.example.com/asfoka']


class TestInfoGetter(TestCase):
    def test_url_to_filename(self):
        results = []
        for url in tests_urls:
            results.append(url_to_filename(url))

        r_0 = results[0]
        for elems in results:
            self.assertEqual(r_0, elems)

    def test_init_InfoGetter(self):
        # Bad path
        self.assertRaises(InvalidFilePath, InfoGetter, 'example.com', 'C:/alfkofkoa')
        self.assertRaises(InvalidFilePath, InfoGetter, 'example.com', 'asfaggag')

        # Good path, no url folder
        InfoGetter('example.org', os.getcwd() + '/dir_check')
        self.assertTrue(os.path.isdir(os.getcwd() + '/dir_check/example - org'))

        # Good path, url folder no json
        InfoGetter('empty', os.getcwd() + '/dir_check')

        # Good path, url folder, bad json
        self.assertRaises(BrokenJsonFile, InfoGetter, 'bad_json', os.getcwd() + '/dir_check')
        # Good path, url folder, good json
        InfoGetter('good_json', os.getcwd() + '/dir_check')

        # No path, no output folder
        InfoGetter('example.com')
        self.assertTrue(os.path.isdir(os.getcwd() + '/output'))
        self.assertTrue(os.path.isdir(os.getcwd() + '/output/example - com'))

        # Create temp files for json check with no path
        os.mkdir(os.getcwd() + '/output/bad_json')
        os.mkdir(os.getcwd() + '/output/good_json')
        with open(os.getcwd() + '/output/bad_json/data.json', 'w') as f:
            f.write('')
        with open(os.getcwd() + '/output/good_json/data.json', 'w') as f:
            f.write('{"a": 1}')

        # No path, bad json
        self.assertRaises(BrokenJsonFile, InfoGetter, 'bad_json')
        # No path, good json
        InfoGetter('good_json')

        # Clean
        os.rmdir(os.getcwd() + '/dir_check/example - org')
        os.remove(os.getcwd() + '/output/bad_json/data.json')
        os.remove(os.getcwd() + '/output/good_json/data.json')
        os.rmdir(os.getcwd() + '/output/bad_json')
        os.rmdir(os.getcwd() + '/output/good_json')
        os.rmdir(os.getcwd() + '/output/example - com')
        os.rmdir(os.getcwd() + '/output')

    def test_sanitize_url(self):
        ig = InfoGetter('example.org')

        results = []
        for url in tests_urls:
            results.append(ig._sanitize_url(url))

        r_0 = results[0]
        for elems in results:
            self.assertEqual(r_0, elems)

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_ip(self):
        ig = InfoGetter('example.org')
        # Check url sanitizing
        results = []
        for url in tests_urls:
            results.append(ig._get_ip(url))

        r_0 = results[0]
        for elems in results:
            self.assertEqual(r_0, elems)

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_title(self):
        ig = InfoGetter('example.org')
        self.assertEqual('Example Domain', ig._get_title(ig.url))

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_estimated_size(self):
        ig = InfoGetter('example.org')
        self.assertEqual(1, ig._get_estimated_size(ig.url)[1])

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_potential_api(self):
        ig = InfoGetter('github.com')
        self.assertEqual('https://api.github.com/', ig._get_potential_api(ig.url))
        ig = InfoGetter('example.org')
        self.assertRaises(NoApi, ig._get_potential_api, ig.url)

        # Clean
        os.rmdir(os.getcwd() + '/output/github - com')
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_news_url(self):
        ig = InfoGetter('example.org')
        self.assertEqual('https://www.google.com/search?tbm=nws&q="example.org"', ig._get_news_url(ig.url))

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_whois_data(self):
        print("[!] Warning, the first part of this test is dependent on no server changes for example.org")
        with open('example_org_whois.json', 'r') as f:
            example_json = json.load(f)

        ig = InfoGetter('example.org')
        self.assertEqual(example_json, ig._get_whois_data(ig.url))

        ig = InfoGetter('clarin.com.ar')
        self.assertRaises(NoWhois, ig._get_whois_data, ig.url)

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output/clarin - com - ar')
        os.rmdir(os.getcwd() + '/output')

    def test_get_geo_location_data(self):
        print("[!] Warning, the first part of this test is dependent on no server changes for example.org")
        with open('example_org_geo_location.json', 'r') as f:
            example_json = json.load(f)

        ig = InfoGetter('example.org')
        self.assertEqual(example_json, ig._get_geo_location_data(ig._get_ip(ig.url)))

        ig = InfoGetter('ahdsfdg.com')
        self.assertRaises(NoGeo, ig._get_geo_location_data, 'ASFKJA')

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output/ahdsfdg - com')
        os.rmdir(os.getcwd() + '/output')

    def test_get_geo_imgs(self):
        print("[!] Warning, this test is dependent on no server changes for example.org")
        correct_response = ['https://maps.google.com/maps?width=100%&height=600&hl=es&q=CA, US&ie=UTF8&t=&z=7&iwloc=B&output=embed',
                            'https://www.google.com/maps/@?api=1&map_action=map&center=42.1596, -70.8217&zoom=13']
        ig = InfoGetter('example.org')
        result = ig._get_geo_imgs(ig._get_whois_data(ig._get_ip(ig.url)), ig._get_geo_location_data(ig._get_ip(ig.url)),
                                ig.filepath)

        self.assertEqual(correct_response, result)

        # Clean
        os.remove(os.getcwd() + '/output/example - org/location.jpg')
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_built_with(self):
        print("[!] Warning, this test is dependent on no changes on example.org")
        correct_response = {'cdn': ['EdgeCast']}
        ig = InfoGetter('example.org')
        self.assertEqual(correct_response, ig._get_built_with(ig.url))

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output')

    def test_get_robot(self):
        print("[!] Warning, this test is dependent on no changes on soundcloud.com")
        with open('soundcloud_com_robots_txt.txt', 'r') as f:
            correct_response = f.read()

        ig = InfoGetter('soundcloud.com')
        self.assertEqual(correct_response, ig._get_robot(ig.url))

        # Clean
        os.rmdir(os.getcwd() + '/output/soundcloud - com')
        os.rmdir(os.getcwd() + '/output')

    def test_get_sitemap(self):
        print("[!] Warning, this test is dependent on no changes on example.org")
        correct_response = 'https://a-v2.sndcdn.com/sitemap.txt'
        ig = InfoGetter('soundcloud.com')
        self.assertEqual(correct_response, ig._get_sitemap(ig.url, ig._get_robot(ig.url)))

        ig = InfoGetter('example.org')

        self.assertRaises(NoSitemap, ig._get_sitemap, ig.url, None)

        # Clean
        os.rmdir(os.getcwd() + '/output/example - org')
        os.rmdir(os.getcwd() + '/output/soundcloud - com')
        os.rmdir(os.getcwd() + '/output')

