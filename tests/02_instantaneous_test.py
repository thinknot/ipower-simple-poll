import requests
import requests_cache

requests_cache.install_cache('egauge_test_cache')

from lxml import etree


def test_get_instant_check_xml_root():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    root = xml_tree.getroot()
    assert (root.tag == 'data')
    assert len(root.attrib) <= 1  # may have 'serial' attribute equal to the config serial number as a hex string


def test_get_instant_check_xml_timestamp():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    timestamp_element = xml_tree.find('./ts')
    assert timestamp_element.text
    int(timestamp_element.text)


def test_get_instant_check_xml_resultrows_exist():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    rrows = xml_tree.findall('./r')
    assert len(rrows) > 0

# Attribute 'rt' may be set to the string 'total' to indicate that the register is
# a total or virtual register whose value has been calculated from the physical (did) registers.


def test_get_instant_check_xml_resultrows_registers():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    rrows = xml_tree.xpath('./r[not(@rt)]')
    assert len(rrows) > 0


def test_get_instant_check_xml_resultrows_totals():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    rrows = xml_tree.findall('./r[@rt="total"]')
    assert len(rrows) > 0


def test_get_instant_check_resultrow_values():
    response = requests.get('http://egauge45930.egaug.es/cgi-bin/egauge?inst&tot')
    response_body_as_xml = etree.fromstring(response.content)
    xml_tree = etree.ElementTree(response_body_as_xml)
    rrows = xml_tree.findall('./r')
    for resultrow in rrows:
        register_type = resultrow.get('t')
        register_name = resultrow.get('n')
        assert len(resultrow) == 2
        for value in resultrow:
            assert (value.tag == 'v' or value.tag == 'i')
            assert(value.text)

# Two sub-elements may appear for each r element: v and i.
# v - A cumulative register value expressed in a type-specific unit.
#     Subtracting two consecutive readings and dividing by the number of seconds elapsed,
#     gives the average rate of change for the register
# i - The average rate of change of the register value as measured for the most recent one-second interval
