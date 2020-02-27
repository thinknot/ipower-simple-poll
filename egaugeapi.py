from builtins import *
from builtins import object
import logging
import httplib2
import datetime as dt
import time
from lxml import etree

from egaugedata import EgaugeData


# basic fetch implementation of http://egauge.net/docs/egauge-xml-api.pdf
class EgaugeApi(object):
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

    #
    # returns
    def get_history_minutes(self, time_begin, time_end=None):
        """
    params
    fromTime: from unix timestamp (newest)
    toTime: to unix timestamp (oldest) [optional]
    """
        # set up and make request
        gw_url = "http://{0}/cgi-bin/egauge-show".format(self.host)

        dt_begin = dt.datetime.fromtimestamp(time_begin, dt.timezone.utc)
        dt_minute = dt_begin - dt.timedelta(seconds=dt_begin.second,
                                            microseconds=dt_begin.microsecond)
        time_begin = time.mktime(dt_minute.timetuple())

        if time_end is None:
            time_end = dt.datetime.utcnow().timestamp()

        ## Notes on HTTP parameters:
        #'/cgi-bin/egauge-show?m&n=2&s=9&C'
        #'/cgi-bin/egauge-show?a&m&T=1581750180,1581750120,1581750060'
        #'/cgi-bin/egauge-show?a&m&T=1581750000,1581797259&C'
        #'/cgi-bin/egauge-show?a&m&f=1581797259&t=1581750000'
        # a - total and virtual registers
        # f - The timestamp of the first (newest) row to be returned
        # t - The timestamp of the last (oldest) row to be returned
        # m - use minutes as units of each row. (other options are h,S,d)
        # s - skip a certain number of rows in the result set
        # C - show deltas between each timestamp row, rather than the actual register value
        if time_begin and time_end:
            params = "?a&m&t={}&f={}".format(int(time_begin), int(time_end))
        else:
            self.logger.error("time_begin is mandatory.")
            return None, None

        response = self.run_egauge_httpquery(gw_url + params)

        resultData = EgaugeData(response)
        self.logger.debug(resultData)

        resultValues = resultData.convert()
        self.logger.debug(resultValues)

        return resultValues

    def get_instant_data(self):
        """
    curl -v --digest  -uuser 'http://egauge30808.egaug.es/cgi-bin/egauge?v1&inst'
    """
        # f - The timestamp of the first (newest) row to be returned
        # t - The timestamp of the last (oldest) row to be returned
        # The data is in descending order

        gw_url = "http://{0}/cgi-bin/egauge?v1&inst&tot".format(self.host)

        # self.logger.debug("Fetching : %s", gw_url)

        content = self.run_egauge_httpquery(gw_url)

        # TODO handle http timeout round here
        if content == None:
            return None

        root = etree.XML(content)

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
                    data['Timestamp'] = egts  # e.g., 1412619506
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

        data['GridEnergyConsumptionInWattSeconds'] = gridEnergy  # grid-powered daily energy in Watt-seconds
        data['GridPowerConsumptionInWatts'] = gridPower  # current grid power consumption in Watts
        data['TotalEnergyConsumptionInWattSeconds'] = abs(loadEnergy)  # Total loads daily energy in Watt-seconds
        data['TotalPowerConsumptionInWatts'] = abs(loadPower)  # Total loads current consumption in Watts
        data['SolarEnergyGenerationInWattSeconds'] = genEnergy  # daily energy generated in Watt-seconds
        data['SolarPowerGenerationInWatts'] = genPower  # current generation in Watts

        return data


    def run_egauge_httpquery(self, url):
        # 'NULL' maps to 'None' in Python
        # It throws an exception in httplib API's, so set it to defaults
        if self.username == None:
            self.username = "owner"
        if self.password == None:
            self.password = "default"

        self.logger.debug(url)

        try:
            req = httplib2.Http(timeout=15)
            req.add_credentials(self.username, self.password)  # Digest Authentication

            response, content = req.request(url,
                                            headers={'Connection': 'Keep-Alive', 'accept-encoding': 'gzip'})

            if response['status'] == '401':
                self.logger.error("Unauthorized request!")
            elif response['status'] == '400':
                self.logger.error("Bad Request!")
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
