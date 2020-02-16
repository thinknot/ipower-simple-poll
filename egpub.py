from influxdb import InfluxDBClient
import time
import os
import logging

from egaugeapi import EgaugeApi

################################################################################
## EGAUGE 
################################################################################

# EGAUGE_HOST = os.getenv("EGAUGE_HOST", "fail")
EGAUGE_ID = 'egauge45930'
EGAUGE_HOST = EGAUGE_ID + '.egaug.es'
EGAUGE_USER = None  # Add username if necessary
EGAUGE_PASS = None  # Add password if necessary

# energy collection interval - last 5 minutes (1min * 60s)
TIME_AGO = 3 * 60
# create a global vars: get Unix timestamps for now, and for 5 minutes ago
now = int(time.time())
then = int(time.time()) - TIME_AGO

################################################################################
## INFLUXDB 
################################################################################

INFLUX_HOST = 'comeaux'
INFLUX_PORT = 8086
INFLUX_DB = 'customer23'
INFLUX_USER = 'gather'
INFLUX_PASS = 'slurp'

################################################################################
## MAIN 
################################################################################

if __name__ == "__main__":
    #    signal.signal(signal.SIGTERM, signal_handler)

    logging.basicConfig(format="[%(asctime)-15s] %(message)s", level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    pid = os.getpid()

    dbClient: InfluxDBClient = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS)

    logger.info("--------------------------------------------------")
    logger.info("Environment")
    logger.info("--------------------------------------------------")

    # logger.info("Log config --> %s", LOG_CONFIG)
    logger.info("INFLUX endpoint --> %s:%s", INFLUX_HOST, INFLUX_PORT)
    logger.info("EGAUGE endpoint --> %s", EGAUGE_HOST)

    logger.info("--------------------------------------------------")
    logger.info("Process ID: %s [%s]", pid, "Debug" if logging.getLogger().getEffectiveLevel() < 20 else "Production");
    logger.info("--------------------------------------------------")

    logger.info("Initializing... %s", now)

    # myEgauge = eGauge(EGAUGE_HOST, EGAUGE_USER, EGAUGE_PASS)
    myEgauge = EgaugeApi(EGAUGE_HOST)

    logger.info("Running...")
    while True:
        now = int(time.time())

        # get historical data every n minutes or so
        if now - then >= TIME_AGO:
            intervalEgaugeData = myEgauge.get_history_minutes(then, now)
            then = now
            meter_id = None
            for meter in intervalEgaugeData['metercatalog']:
                if meter['meterName'] == 'Main':
                    meter_id = meter['meterId']
                    break
            if meter_id is not None:
                for reading in intervalEgaugeData['readings']:
                    if reading['meterId'] == meter_id:
                        influx_line = "energy,equipment_id={} energy_load={} {}".format(
                            EGAUGE_ID,
                            float(reading['value']),
                            reading['timestamp'] * 1000000000)
                        logger.debug(influx_line)
                        dbClient.write(influx_line, {'db': INFLUX_DB}, protocol='line')

        # get instant data
        instantEGaugeData = myEgauge.get_instant_data()
        if instantEGaugeData == None:
            continue

#        gridPower = instantEGaugeData['GridPowerConsumptionInWatts']  # current grid power consumption in Watts
        loadPower = instantEGaugeData['TotalPowerConsumptionInWatts']  # Total loads current consumption in Watts
#        solarPower = instantEGaugeData['SolarPowerGenerationInWatts']  # current generation in Watts

        # logger.debug(instantEGaugeData)
        # logger.info("It's Data!   loadPower: %s   gridPower: %s   solarPower: %s", loadPower, gridPower, solarPower)

        loadEnergy = instantEGaugeData['TotalEnergyConsumptionInWattSeconds'] # total Watt-seconds counter

        # Use Influx line protocol for now, it has the format:
        #    measurement,tag_set field_set timestamp
        # https://docs.influxdata.com/influxdb/v1.7/write_protocols/line_protocol_tutorial/

        influx_line = "power,equipment_id={} power_load={}".format(
            EGAUGE_ID,
            loadPower)

        result = dbClient.write([influx_line], {'db': INFLUX_DB}, protocol='line')

        # Sleep a total 5 seconds between iterations
        time.sleep(6)

    # end while "True"
