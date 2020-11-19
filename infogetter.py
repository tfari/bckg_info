import os
import json
import socket
import re
import whois
import builtwith
import time
import datetime
from bs4 import BeautifulSoup

from helpers.req_handler import GET, RequestHandler, RequestErrorData, RequestData

"""
Gather the following information out of a given domain:
    - URL
    - IP
    - TITLE
    - ESTIMATED SIZE
    - POTENTIAL API
    - LINK TO LATEST NEWS
    - WHOIS INFORMATION
    - WHOIS-DATA BASED GOOGLE MAPS IMAGE AND LINK
    - GEOLOCATION INFORMATION
    - GEOLOCATION-DATA BASED GOOGLE MAPS IMAGE AND LINK
    - BUILTWITH INFORMATION
    - ROBOTS.TXT 
    - SITEMAP 
    - WIKI PAGE
"""


INVALID_FILENAME_CHARS = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.']


def url_to_filename(url):
    """
    Transform an url into a filename valid name

    :param url: str
    :return: str
    """

    # Standardize urls
    first_pass = url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
    # Cut to root
    second_pass = first_pass.replace('.', ' - ')
    # Remove invalids
    for invalid in INVALID_FILENAME_CHARS:
        second_pass = second_pass.replace(invalid, '')

    return second_pass


class InfoGetter(object):
    """
    Class to handle the information gathering.

    It is instantiated with an url and an optional output_directory (it defaults to ./output), and then it is used
    by calling on .run(), it saves (and returns) the data gotten in the form of a dictionary.

    We use a class instead of pure static methods for refactoring reasons, specifically involving the persistent
    RequestData, RequestErrorData, and RequestHandler instances, as well as the collection of the data and the handling
    of situations in which the data is already saved and we want to avoid repeating the scraping.

    However, we let  most of the methods operate as static methods for the sake of testing. The .run() method then
    stitches them together and is in charge of the strategy behind handling the possible errors and empty results
    accordingly.

    """

    def __init__(self, url, output_directory=None):
        """
        Takes care of handling path and file checks and creations, as well as checking if there's already valid data
        saved about this domain.

        :param url: str
        :param output_directory: str (defaults to ./output)
        """

        # Instantiate instance vars
        self.url = url
        self.data = {}
        self.loaded_flag = False
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
        self.requester = RequestHandler([''], RequestData(GET, headers=headers), RequestErrorData(allow_errors=False))

        # output_directory checks
        default_path = os.getcwd() + '/output'
        if output_directory and not os.path.isdir(output_directory):
            raise InvalidFilePath(output_directory)

        if not output_directory:
            if not os.path.isdir(default_path):
                os.mkdir(default_path)
            output_directory = default_path

        # Url specific directory check
        url_folder_path = output_directory + '/' + url_to_filename(self.url)
        if not os.path.isdir(url_folder_path):
            os.mkdir(url_folder_path)

        else:  # Check if file already exists
            if os.path.isfile(url_folder_path + '/data.json'):

                try:  # Handle bad json
                    with open(url_folder_path + '/data.json', 'r') as json_file:
                        self.data = json.load(json_file)
                    self.loaded_flag = True
                except json.decoder.JSONDecodeError as e:
                    raise BrokenJsonFile(repr(e))

        self.filepath = url_folder_path

    def run(self):
        """
        Stitch together all different calls, while handling the different raises that might occur.

        If self.loaded_flag is True, return the saved self.data without performing any work.

        :return: dict, self.data
        """
        # Check the flag
        if self.loaded_flag:
            return self.data

        # First
        self.data['url'] = self.url

        # Do not catch errors at IP lookup, as it might indicate connection issues or bad URLs.
        self.data['ip'] = self._get_ip(self.url)

        # If IP lookup didn't raise an error, this shouldn't either
        self.data['title'] = self._get_title(self.url)

        # But this might if google changed structure
        try:
            self.data['estimated'] = self._get_estimated_size(self.url)
        except Exception as e:
            err = ("[!] Possible Google structure change: _get_estimated_size failed with exception: %s" % str(e))
            print("%s" % err)
            self.data['estimated'] = ('Error', err)

        # Get potential API, catch if none
        try:
            self.data['potential_api'] = self._get_potential_api(self.url)
        except NoApi:
            self.data['potential_api'] = None

        # Save news_url
        self.data['news_url'] = self._get_news_url(self.url)

        # Get whois, if error try with IP, else catch error
        try:
            self.data['whois'] = self._get_whois_data(self.url)
        except NoWhois:
            try:
                self.data['whois'] = self._get_whois_data(self.data['ip'])
            except NoWhois:
                self.data['whois'] = None

        # Get geolocation, catch both API fails and broader IP fails
        try:
            self.data['geo_location'] = self._get_geo_location_data(self.data['ip'])
        except NoGeo:
            print("[!] Geo Location lookup failed: It shouldn't fail if IP lookup came right.")
            self.data['geo_location'] = None
        except GeoAPIFailed:
            print("[!] Geo Location lookup failed on the request lvl, API might have changed or is down.")

        # Get images, handle google hiccups
        try:
            self.data['geo_maps'] = self._get_geo_imgs(self.data['whois'], self.data['geo_location'], self.filepath)
        except GoogleHiccup:
            time.sleep(2)
            try:
                self.data['geo_maps'] = self._get_geo_imgs(self.data['whois'], self.data['geo_location'], self.filepath)
            except GoogleHiccup:
                self.data['geo_maps'] = None

        # Call builtwith
        self.data['builtwith'] = self._get_built_with(self.url)

        # Get robots.txt if any
        try:
            self.data['robots'] = self._get_robot(self.url)
        except:
            self.data['robots'] = None

        # Get sitemap if any
        try:
            self.data['sitemap'] = self._get_sitemap(self.url, self.data['robots'])
        except NoSitemap:
            self.data['sitemap'] = None

        # Get wiki page if any
        try:
            self.data['wiki'] = self._get_wiki(self.url)
        except NoWiki:
            self.data['wiki'] = None

        # Save data
        with open(self.filepath + '/data.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, indent=True))

        # Return data
        return self.data

    def _req_wrap(self, url):
        """
        Wraps Request flushing, calling on new url, and response gathering.

        :param url: str
        :return: request's ResponseObject
        """

        self.requester.url_list = [url]
        self.requester.responses = []
        self.requester.run()

        return self.requester.responses[0]

    @staticmethod
    def _sanitize_url(url):
        """
        Returns a root url without http/https and/or www.

        :param url: str
        :return: str
        """
        return url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

    def _get_ip(self, url):
        """
        Get url IP via socket library

        :param url: str
        :return: str
        """

        try:
            ip = socket.gethostbyname(self._sanitize_url(url))
            return ip
        except socket.gaierror:
            raise BadUrlAtIPLookUp(url)

    def _get_title(self, url):
        """
        Get website title via BeautifulSoup

        :param url: str
        :return: str
        """

        sanitized_url = 'http://' + self._sanitize_url(url)
        r = self._req_wrap(sanitized_url)

        title = BeautifulSoup(r.text, 'html.parser').title.string
        return title

    def _get_estimated_size(self, url):
        """
        Estimate size of website using a google query with site:

        :param url: str
        :return: (str, int) -> (estimated size url, estimated size)
        """

        google_query_url = 'https://www.google.com/search?q=site:%s' % self._sanitize_url(url)
        r = self._req_wrap(google_query_url)

        bs_result_stats = BeautifulSoup(r.text, 'html.parser').find('div', {'id': 'result-stats'}).getText()
        bs_num = re.findall(re.compile('[0-9,]+'), bs_result_stats)[0].replace(',', '')
        return google_query_url, int(bs_num)

    def _get_potential_api(self, url):
        """
        Gets a potential URL for an API using a google query.

        Raise NoApi if the first result in the query doesn't share domain with the URL.

        :param url: str
        :return:str
        """

        google_query_url = 'https://www.google.com/search?q=api %s' % self._sanitize_url(url)
        r = self._req_wrap(google_query_url)

        bs_search_results = BeautifulSoup(r.text, 'html.parser').findAll('div', {'id': 'search'})[0]
        bs_first_result = bs_search_results.find('cite').find(text=True, recursive=False)

        # Check its API
        if bs_first_result.find(self._sanitize_url(url)) != -1:
            return bs_first_result
        else:
            raise NoApi()

    def _get_news_url(self, url):
        """
        Get a google news query for the domain

        :param url: str
        :return: str
        """

        return 'https://www.google.com/search?tbm=nws&q="%s"' % self._sanitize_url(url)

    @staticmethod
    def _get_whois_data(ip):
        """
        Get whois data on the ip

        :param ip: str
        :return: dict
        """

        whois_flat = {}
        try:
            whois_data = whois.whois(ip)
        except socket.gaierror:
            raise NoWhois()

        # whois returns datetime objects, we want to flatten them into strings to then save as .json
        for key in whois_data.keys():
            if isinstance(whois_data[key], datetime.datetime):
                whois_flat[key] = str(whois_data[key])
            elif isinstance(whois_data[key], list):  # They can appear within lists
                elem_list = []
                for elem in whois_data[key]:
                    if isinstance(elem, datetime.datetime):
                        elem_list.append(str(elem))
                    else:
                        elem_list.append(elem)
                whois_flat[key] = elem_list
            else:
                whois_flat[key] = (whois_data[key])

        return whois_flat

    def _get_geo_location_data(self, ip):
        """
        Use extreme-ip-lookup API to get geo_location data

        :param ip: str
        :return: dictionary
        """
        geo_url = 'http://extreme-ip-lookup.com/json/%s' % ip
        r = self._req_wrap(geo_url)
        try:
            if r.json()['status'] == 'fail':
                raise NoGeo()
            else:
                return r.json()
        except KeyError:
            raise GeoAPIFailed()

    def _get_geo_imgs(self, whois_data, geolocation_data, filepath):
        """
        Get the iframe link of the location gotten through whois_data.
        Save a static image and google maps link gotten through geolocation_data.

        :param whois_data: dict
        :param geolocation_data: dict
        :return: list, [whois_google_maps_embed_link, geo_location_google_maps_link]
        """
        response = [None, None]

        if whois_data:
            if whois_data['address'] and whois_data['zipcode']:
                data = whois_data['address'] + ' ' + whois_data['zipcode']
            else:
                data = ''
                if whois_data['city']:
                    data += whois_data['city'] + ', '
                if whois_data['state']:
                    data += whois_data['state'] + ', '
                if whois_data['country']:
                    data += whois_data['country']

            if data != '':
                # Make google maps link
                google_maps_link = "https://maps.google.com/maps?width=100%&height=600&hl=es&q=" + data + \
                                   "&ie=UTF8&t=&z=7&iwloc=B&output=embed"
                response[0] = google_maps_link

        #

        if geolocation_data:
            im_query_url = 'http://www.google.com/search?q=%s,%s' % (geolocation_data['lat'], geolocation_data['lon'])

            r = self._req_wrap(im_query_url)

            try:
                map_url = (re.findall(re.compile('/maps/vt.*'), r.text)[0]).split('"')[0]
                map_query = 'http://google.com%s' % map_url

                img = self._req_wrap(map_query)

                with open('%s/location.jpg' % filepath, 'wb') as f:
                    f.write(img.content)

            except IndexError:
                raise GoogleHiccup()

            google_maps_geolocation = 'https://www.google.com/maps/@?api=1&map_action=map&center=%s, %s&zoom=13' % \
                                      (geolocation_data['lat'], geolocation_data['lon'])
            response[1] = google_maps_geolocation

        return response

    def _get_built_with(self, url):
        """
        Get builtwith data of the url

        :param url: str
        :return: dict
        """
        #
        sanitized_url = 'http://' + self._sanitize_url(url)
        r = self._req_wrap(sanitized_url)

        return builtwith.builtwith('aaa', headers=r.headers, html=str(r.text).encode('utf-8'))

    def _get_robot(self, url):
        """
        Get robots.txt data of the url

        :param url: str
        :return: str
        """
        sanitized_url = 'http://' + self._sanitize_url(url)

        r = self._req_wrap('%s/robots.txt' % sanitized_url)

        return r.text

    def _get_sitemap(self, url, robot_data):
        """
        Get sitemap data of the url

        :param url:
        :return:
        """

        # Check for sitemap uri in robot_data
        robot_dict = {}
        if robot_data:
            robot = robot_data.split('\n')
            for elem in robot:
                split_elem = elem.split(':')

                try:
                    robot_dict[split_elem[0]] = split_elem[1:]
                except IndexError:
                    pass

        # Get (and try) link
        if robot_dict.get('Sitemap'):
            sitemap_url = ':'.join(robot_dict['Sitemap']).lstrip()
        else:
            sitemap_url = 'http://' + self._sanitize_url(url) + '/sitemap.xml'

        try:
            self._req_wrap(sitemap_url)  # We do this to catch exceptions if sitemap_url does not work
            return sitemap_url
        except:
            raise NoSitemap()

    def _get_wiki(self, url):
        """
        # Get potential wiki url for the url by using a google query.

        :param url: str
        :return: str
        """
        google_query = 'https://www.google.com/search?q=%s site:wikipedia.org' % self._sanitize_url(url)

        r = self._req_wrap(google_query)

        bs_search_results = BeautifulSoup(r.text, 'html.parser').findAll('div', {'id': 'search'})[0]
        bs_first_result = bs_search_results.find('a')

        # Make sure it is wiki
        if not bs_first_result:
            raise NoWiki()

        return bs_first_result.get('href')


# Exceptions
class InvalidFilePath(Exception):
    pass


class BrokenJsonFile(Exception):
    pass


class BadUrlAtIPLookUp(Exception):
    pass


class GoogleHiccup(Exception):
    pass


class NoApi(Exception):
    pass


class NoWiki(Exception):
    pass


class NoWhois(Exception):
    pass


class NoGeo(Exception):
    pass


class GeoAPIFailed(Exception):
    pass


class NoSitemap(Exception):
    pass
