import requests
import logging
from csv import reader

M2WEB_URI = 'https://m2web.talk2m.com/t2mapi/'
# this is issued by Talk2M
TALK2M_DEV_ID = "6e713126-7e82-407f-9140-7462d2d5cf00"

EWON_USER = 'Caleb'
EWON_PASS = 'C@13biP0w3r'
EWON_URI = 'get/Ehrlich+Toyota/rcgi.bin/ParamForm?AST_Param='
EWON_PARAMS = '$dtIV$ftT&t2'

# Ehrlich+Toyota Ewon id is 793680
# Ewon pool id is 210312

class M2web(object):
    def __init__(self, account, username, password):
        self.logger = logging.getLogger("__name__")
        self.accountName = account
        self.username = username
        self.password = password
        self.logger.info("M2WEB endpoint --> %s", M2WEB_URI)

    def query_ewon_ebd(self, command, ewon_user, ewon_pass):
        r = requests.post(
            command,
            data={
                't2maccount': self.accountName,
                't2musername': self.username,
                't2mpassword': self.password,
                't2mdeveloperid': TALK2M_DEV_ID,
                't2mdeviceusername': ewon_user,
                't2mdevicepassword': ewon_pass
            }
        )
        return r

    def get_instant_data(self):
        query_url = "{0}{1}{2}".format(M2WEB_URI, EWON_URI, EWON_PARAMS)
        response = self.query_ewon_ebd(query_url, EWON_USER, EWON_PASS)

        if response.status_code != 200:
            return None

        f = (line.decode('utf-8') for line in response.iter_lines())
        csv_reader = reader(f, delimiter=';', quotechar='"')
        result = list(csv_reader)

        data = {}
        try:
            data['SolarPowerInWatts'] = float(result[17][2]) * -1000.0
            data['AmbientTempInDegreesF'] = float(result[24][2])
            data['Irradiance'] = int(result[25][2])
            data['WindSpeed'] = float(result[27][2])
            data['Inverter1PowerInWatts'] = float(result[71][2])
            data['Inverter2PowerInWatts'] = float(result[72][2])
            data['Inverter3PowerInWatts'] = float(result[73][2])
            data['Inverter4PowerInWatts'] = float(result[74][2])
            data['Inverter5PowerInWatts'] = float(result[75][2])
            data['Inverter6PowerInWatts'] = float(result[76][2])
        except IndexError:
#            logger.error("Bad Data trying to parse M2Web CSV")
            return None

        return data
