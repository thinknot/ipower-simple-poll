import requests
import requests_cache

requests_cache.install_cache('egauge_test_cache')

from lxml import etree


def test_get_history_check_xml_rootnode():
    response = requests.get('http://10.0.0.47/cgi-bin/egauge-show')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    root = xml_tree.getroot()
    assert (root.tag == 'group')
    assert len(root.attrib) <= 1  # may have 'serial' attribute equal to the config serial number as a hex string


def test_get_history_check_xml_datanode():
    response = requests.get('http://10.0.0.47/cgi-bin/egauge-show')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    datanode = xml_tree.find('./data')
    assert(datanode is not None)
    assert(datanode.get('columns'))
    assert (datanode.get('time_stamp'))
    assert (datanode.get('time_delta'))
    assert (datanode.get('epoch'))


def test_get_history_check_xml_columns():
    response = requests.get('http://10.0.0.47/cgi-bin/egauge-show')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    cols = xml_tree.findall('./data/cname')
    assert(len(cols) == int(xml_tree.find('./data').get('columns')))
    for col in cols:
        assert (col.get('t'))
        assert (col.text)


def test_get_history_check_xml_rows():
    response = requests.get('http://10.0.0.47/cgi-bin/egauge-show')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    numcols = int(xml_tree.find('./data').get('columns'))
    rows = xml_tree.findall('./data/r')
    assert(len(rows) > 0)
    for row in rows:
        cols = row.getchildren()
        assert(len(cols) == numcols)
        for col in cols:
            assert(col.text)

