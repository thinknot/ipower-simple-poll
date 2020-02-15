from influxdb import InfluxDBClient
from m2web import M2web

import time
import logging
import os

################################################################################
## M2WEB
################################################################################
TALK2M_ACCOUNT = 'ageto.ipower'
M2WEB_USER = 'Caleb'
M2WEB_PASS = 'C@13biP0w3r'

################################################################################
## INFLUXDB
################################################################################
INFLUX_HOST = 'localhost'
INFLUX_PORT = 8086
INFLUX_DB = 'greeley'
INFLUX_USER = 'greeley_poll'
INFLUX_PASS = 'FpMK6RamNX'

################################################################################
## MAIN
################################################################################

# last 5 minutes (1min * 60s)
TIME_AGO = 5 * 60
# get Unix timestamps for now, and now-time_ago
now = int(time.time())
then = int(time.time()) - TIME_AGO

if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_handler)
    pid = os.getpid()

    logging.basicConfig(format="[%(asctime)-15s] %(message)s", level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Initializing... %s", now)

    dbClient = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS)

    logger.info("--------------------------------------------------")
    logger.info("Environment")
    logger.info("--------------------------------------------------")

#    logger.info("Log config --> %s", LOG_CONFIG)
#    logger.info("MQTT endpoint --> %s:%s", MQTT_HOST_NAME, MQTT_HOST_PORT)
    logger.info("INFLUX endpoint --> %s:%s", INFLUX_HOST, INFLUX_PORT)

    logger.info("--------------------------------------------------")
    logger.info("Process ID: %s [%s]", pid, "Debug" if logging.getLogger().getEffectiveLevel() < 20 else "Production")
    logger.info("--------------------------------------------------")

    myEwon = M2web(TALK2M_ACCOUNT, M2WEB_USER, M2WEB_PASS)
    logger.info("Running...")

    while True:
        now = int(time.time())
        if now - then >= TIME_AGO:
            then = now

        # get instant data
        instantEwonData = myEwon.get_instant_data()
        if instantEwonData == None:
            continue

        solarPower = instantEwonData['SolarPowerInWatts']
#        logger.info("It's Data!     solarPower: %s", solarPower)

        influx_line_power = "power,equipment_id=ewon793680 power_solar={}".format(solarPower)

        result = dbClient.write([influx_line_power], {'db': INFLUX_DB}, protocol='line')
       

        inv1 = instantEwonData['Inverter1PowerInWatts']
        inv2 = instantEwonData['Inverter2PowerInWatts']
        inv3 = instantEwonData['Inverter3PowerInWatts']
        inv4 = instantEwonData['Inverter4PowerInWatts']
        inv5 = instantEwonData['Inverter5PowerInWatts']
        inv6 = instantEwonData['Inverter6PowerInWatts']

        influx_line_inverters = "power,equipment_id=ewon793680 power_inv1={},power_inv2={},power_inv3={},power_inv4={},power_inv5={},power_inv6={}".format(
            inv1,
            inv2,
            inv3,
            inv4,
            inv5,
            inv6)

        result = dbClient.write([influx_line_inverters], {'db': INFLUX_DB}, protocol='line')


        temp = instantEwonData['AmbientTempInDegreesF']
        irradiance = instantEwonData['Irradiance']
        windspeed = instantEwonData['WindSpeed']

        influx_line_weather = "weather,equipment_id=ewon793680 temp={},irradiance={},windspeed={}".format(
            temp,
            irradiance,
            windspeed)

        result = dbClient.write([influx_line_weather], {'db': INFLUX_DB}, protocol='line')

        # Sleep a total 5 seconds between iterations
        time.sleep(6)
    # end while "True"
