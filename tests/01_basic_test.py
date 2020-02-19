import requests
import requests_cache

requests_cache.install_cache('egauge_test_cache')

from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from lxml import etree


def test_get_instant_check_status_code_equals_200():
    response = requests.get('http://egauge45930.d.egauge.net/cgi-bin/egauge?inst&tot')
    assert response.status_code == 200


def test_get_instant_check_content_type_equals_xml():
    response = requests.get('http://egauge45930.d.egauge.net/cgi-bin/egauge?inst&tot')
    assert response.headers['Content-Type'] == 'text/xml; charset=utf-8'


def test_get_instant_check_content_xml_is_well_formed():
    parser = make_parser()
    parser.setContentHandler(ContentHandler())
    try:
        parser.parse('http://egauge45930.d.egauge.net/cgi-bin/egauge?inst&tot')
    except Exception:
        assert False


def test_get_instant_check_xml_syntax_is_valid():
    try:
        doc = etree.parse('http://egauge45930.d.egauge.net/cgi-bin/egauge?inst&tot')
    except etree.XMLSyntaxError:
        assert False


def test_get_history_check_status_code_equals_200():
        response = requests.get('http://egauge45930.d.egauge.net/cgi-bin/egauge-show')
        assert response.status_code == 200


def test_get_history_check_content_type_equals_xml():
        response = requests.get('http://egauge45930.d.egauge.net/cgi-bin/egauge-show')
        assert response.headers['Content-Type'] == 'text/xml; charset=utf-8'


def test_get_history_check_content_xml_is_well_formed():
        parser = make_parser()
        parser.setContentHandler(ContentHandler())
        try:
            parser.parse('http://egauge45930.d.egauge.net/cgi-bin/egauge-show')
        except Exception:
            assert False


def test_get_history_check_xml_syntax_is_valid():
        try:
            doc = etree.parse('http://egauge45930.d.egauge.net/cgi-bin/egauge-show')
        except etree.XMLSyntaxError:
            assert False


def test_get_history_check_xml_dtd_schema():
    pass


