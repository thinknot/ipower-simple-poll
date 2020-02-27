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

# short collection interval for power / counters - 6 seconds
EGAUGE_POLL_INSTANT = 6
# longer collection interval for energy intervals - 3 minutes * 60s
EGAUGE_POLL_HISTORY = 3 * 60
# create global vars for two Unix timestamps
now = int(time.time())
then = now - EGAUGE_POLL_HISTORY  # 180 seconds ago

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
    logger.info("Process ID: %s [%s]", pid, "Debug" if logging.getLogger().getEffectiveLevel() < 20 else "Production")
    logger.info("--------------------------------------------------")

    logger.info("Initializing... %s", now)

    # myEgauge = eGauge(EGAUGE_HOST, EGAUGE_USER, EGAUGE_PASS)
    myEgauge = EgaugeApi(EGAUGE_HOST)

    logger.info("Running...")
    while True:
        if now - then >= EGAUGE_POLL_HISTORY:
            # get historical data every 3 minutes or so
            intervalEgaugeData = myEgauge.get_history_minutes(then)
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
                            reading['timestamp'] * 1000000000)  # in nanoseconds!
                        logger.debug(influx_line)
                        dbClient.write(influx_line, {'db': INFLUX_DB}, protocol='line')
            then = now

        # get instant data every poll interval
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

        # Sleep arbitrary 6 seconds between poll iterations
        time.sleep(EGAUGE_POLL_INSTANT)
        now = int(time.time())
    # end while "True"
