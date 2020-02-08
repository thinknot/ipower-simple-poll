#from __future__ import unicode_literals
#from __future__ import print_function
#from __future__ import division
#from __future__ import absolute_import
#from future import standard_library
#standard_library.install_aliases()
from builtins import *
from builtins import object
import logging
import httplib2
from datetime import datetime
import calendar
from lxml import etree as ET


class eGauge(object):
  def __init__(self, host, username, password):
    self.logger = logging.getLogger("__name__")
    self.host = host
    self.username = username
    self.password = password

  def __init__(self, host):
    self.logger = logging.getLogger("__name__")
    self.host = host
    self.username = None
    self.password = None

  def parse_datetime(str) :
    if str == None :
      return None
    try :
      return datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
    except ValueError :
      try :
        return datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
      except ValueError :
        return datetime.strptime(str, "%Y-%m-%d")
  def get_ts(dt):
      return calendar.timegm(dt.utctimetuple())

  #
  # basic fetch implementation of http://egauge.net/docs/egauge-xml-api.pdf
  #
  def getDataByRange(self, fromTime, toTime=None):
    """
    curl -v --digest  -uuser
    'http://egauge30808.egaug.es/cgi-bin/egauge-show?a&T=1412319600'
    'http://egauge30808.egaug.es/cgi-bin/egauge-show?a&m&s=4&f=1412346900&t=1412345700'

    params
    fromTime: from unix timestamp (newest)
    toTime: to unix tsimestmp (oldest) [optional]
    """
    # The data is in decending order

    # set up and make request
    gw_url = "http://{0}/cgi-bin/egauge-show".format(self.host)

    # note on HTTP parameters: 
    # a - total and virtual registers
    # T - comma separated list of timestamps, from youngest to oldest
    # f - The timestamp of the first (newest) row to be returned
    # t - The timestamp of the last (oldest) row to be returned
    # m -
    # s - 
    if fromTime and toTime:
      params = "?a&T={},{}".format(fromTime, toTime)
#      params = "?f={0}&t={1}&a&m&s=4".format(fromTime, toTime)
    elif fromTime:
      params = "?a&T={0}".format(fromTime)
    else:
      self.logger.error("fromTime is mandatory.")
      return None, None

    response = self.runEgaugeQuery(gw_url + params)
    # create an ElementTree with the HTML response
    root = ET.fromstring(response)
    useDataIndex = -1
    indexToName = {}
    nameToValue = {}
    returnVal = {"gen": -1, "use": -1, "Grid": -1}

    try:
        for child in root[0]:
          if child.tag == "cname":
            useDataIndex += 1
            indexToName[useDataIndex] = child.text

            # logger.debug("childtext - %s", child.text)

          if -1 != useDataIndex and child.tag == "r":
            # special case at/around midnight where data
            # is embedded with column definition data
            # as a row element
            foundUseData = True

            for i in range(useDataIndex + 1):
              key = indexToName[i]
              val = int(child[i].text)
              nameToValue[key] = val

              # logger.debug("childcolval[%s] - %s", key, val)

        if not foundUseData:
          # didn't hit special case above, so data is in its
          # own row
          for child in root[1]:
            if -1 != useDataIndex and child.tag == "r":
              foundUseData = True

              for i in range(useDataIndex + 1):
                key = indexToName[i]
                val = int(child[i].text)
                nameToValue[key] = val

                self.logger.debug("childrowval[%s] - %s", key, val)

        self.logger.debug("[getDataByRange - DATA] : %s", nameToValue)
    except Exception as e:
        self.logger.error("[getDataByRange] - ERROR\n%s", e)

    if foundUseData:
        returnVal["use"] = nameToValue["use"]
        returnVal["gen"] = nameToValue["gen"]
        returnVal["Grid"] = nameToValue["Grid"]

    self.logger.debug("[getDataByRange] - Result: %s", returnVal)

    return returnVal


  def getInstantData(self):
    """
    curl -v --digest  -uuser
    'http://egauge30808.egaug.es/cgi-bin/egauge?v1&inst'
    """
    # f - The timestamp of the first (newest) row to be returned
    # t - The timestamp of the last (oldest) row to be returned
    # The data is in decending order

    gw_url = "http://{0}/cgi-bin/egauge?v1&inst&tot".format(self.host)

    #self.logger.debug("Fetching : %s", gw_url)

    content = self.runEgaugeQuery(gw_url)

    #TODO handle http timeout round here
    if content == None:
        return None

    root = ET.XML(content)


    data = {}
    gridPower = 0
    gridEnergy = 0
    loadPower = 0
    loadEnergy = 0
    genPower = 0
    genEnergy = 0

    try:
        for child in root:
            if child.tag == "ts":
                    egts = int(child.text)
#                    pvodt = timestampToPVODateTime(egts)
                    data['Timestamp'] = egts # e.g., 1412619506
#                    data['PVODate'] = pvodt[0] # e.g., 20141006
#                    data['PVOTime'] = pvodt[1] # e.g., 11:18
            elif child.tag == "r" and child.get("n") == "Grid":
                    for grandchild in child:
                            if grandchild.tag == 'v':
                                    gridEnergy += int(grandchild.text)
                            elif grandchild.tag == "i":
                                    gridPower += int(grandchild.text)
            elif child.tag == "r" and child.get("n") == "Total Usage":
                    for grandchild in child:
                            if grandchild.tag == 'v':
                                    loadEnergy += int(grandchild.text)
                            elif grandchild.tag == "i":
                                    loadPower += int(float(grandchild.text))
            elif child.tag == "r" and child.get("n") == "Solar+":
                    for grandchild in child:
                            if grandchild.tag == 'v':
                                    genEnergy += int(grandchild.text)
                            elif grandchild.tag == "i":
                                    genPower += int(grandchild.text)
    except Exception as e:
            self.logger.error("[processEGaugeInstantData] - Error parsing data: %s", e)
#                logger.error("[processEGaugeInstantData] - BAD DATA\n%s", content)

    data['GridEnergyConsumptionInWattSeconds'] = gridEnergy # grid-powered daily energy in Watt-seconds
    data['GridPowerConsumptionInWatts'] = gridPower # current grid power consumption in Watts
    data['TotalEnergyConsumptionInWattSeconds'] = abs(loadEnergy) # Total loads daily energy in Watt-seconds
    data['TotalPowerConsumptionInWatts'] = abs(loadPower) # Total loads current consumption in Watts
    data['SolarEnergyGenerationInWattSeconds'] = genEnergy # daily energy generated in Watt-seconds
    data['SolarPowerGenerationInWatts'] = genPower # current generation in Watts

    return data


  def runEgaugeQuery(self, url):
    # 'NULL' maps to 'None' in Python
    # It throws an exception in httplib API's, so set it to defaults
    if self.username == None:
      self.username = "owner"
    if self.password == None:
      self.password = "default"

    try:
      req = httplib2.Http(timeout=15)
      req.add_credentials(self.username, self.password)   # Digest Authentication

      response, content = req.request(url,
                headers={'Connection': 'Keep-Alive', 'accept-encoding': 'gzip'})

      if response['status'] == '401':
        self.logger.error("Unauthorized request!")
      elif response['status'] == '400':
        self.logger.error( "Bad Request!")
      elif response['status'] == '500':
        self.logger.error("Internal Error!")
      elif response['status'] == '408':
        self.logger.error("Request timeout!")
      elif response['status'] == '404':
        self.logger.error("Device not found. Probably it is not up")

      if response['status'] != '200':
        self.logger.error("Bad response: %s", response['status'])
        return None

    except Exception as e:
      self.logger.error("[EGAUGE getInstantData] - BAD RESPONSE: %s", e)
      return None

    return content