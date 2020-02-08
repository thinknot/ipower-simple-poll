#import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import random
import time
import requests
import os
import logging

from egauge import eGauge

################################################################################
## EGAUGE 
################################################################################

#EGAUGE_HOST = os.getenv("EGAUGE_HOST", "fail")
EGAUGE_HOST = 'egauge30808.egaug.es'
EGAUGE_USER     = None  # Add username if necessary
EGAUGE_PASS     = None  # Add password if necessary

#last 5 minutes (1min * 60s)
TIME_AGO = 5*60
# get Unix timestmaps for now, and now-time_ago
now  = int(time.time())
then = int(time.time()) - TIME_AGO

################################################################################
## INFLUXDB 
################################################################################

INFLUX_HOST = 'localhost'
INFLUX_PORT = 8086
INFLUX_DB = 'boulder'
INFLUX_USER = 'egaugepoll'
INFLUX_PASS = 'GUi8Y5OSUF'

################################################################################
## MQTT 
################################################################################

MQTT_HOST_NAME = os.getenv("MQTT_HOST_NAME", "localhost")
MQTT_HOST_PORT = int(os.getenv("MQTT_HOST_PORT", "1883"))
MQTT_HOST_KEEP_ALIVE = 60

# MQTT Publishing Topics
MQTT_TOPIC_EGAUGE = "meters/egauge/power/"

def mqtt_host_on_connect(client, userdata, flags, rc):
        logger.info("[MQTT_HOST][Connection] Result ==> %s" % rc)

# publish callback function
def mqtt_host_on_publish(client, userdata, result):
    #logger.info("[MQTT_HOST][Publish]")
    pass

################################################################################
## MAIN 
################################################################################

if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_handler)

    logging.basicConfig(format="[%(asctime)-15s] %(message)s", level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    pid = os.getpid()

    dbClient = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS)

    logger.info("--------------------------------------------------")
    logger.info("Environment")
    logger.info("--------------------------------------------------")

#    logger.info("Log config --> %s", LOG_CONFIG)
#    logger.info("MQTT endpoint --> %s:%s", MQTT_HOST_NAME, MQTT_HOST_PORT)
    logger.info("INFLUX endpoint --> %s:%s", INFLUX_HOST, INFLUX_PORT)
    logger.info("EGAUGE endpoint --> %s", EGAUGE_HOST)

    logger.info("--------------------------------------------------")
    logger.info("Process ID: %s [%s]", pid, "Debug" if logging.getLogger().getEffectiveLevel() < 20 else "Production");
    logger.info("--------------------------------------------------")

    logger.info("Initializing... %s", now)

    #myEgauge = eGauge(EGAUGE_HOST, EGAUGE_USER, EGAUGE_PASS)
    myEgauge = eGauge(EGAUGE_HOST)

    # MQTT_HOST: subscribe to all topics
#    myMQTT = mqtt.Client()
#    myMQTT.username_pw_set("rabbitmq", password='rabbitmq')
#    myMQTT.on_connect = mqtt_host_on_connect
#    myMQTT.on_publish = mqtt_host_on_publish

#    myMQTT.connect(MQTT_HOST_NAME, MQTT_HOST_PORT, MQTT_HOST_KEEP_ALIVE)
#    myMQTT.loop_start()

    logger.info("Running...")
    while True:
        now = int(time.time())

        if now - then >= TIME_AGO:
    #        myEgauge.getDataByRange(then, now)
            then = now

        # get instant data
        instantEGaugeData = myEgauge.getInstantData()
        if instantEGaugeData == None:
            continue

        gridPower = instantEGaugeData['GridPowerConsumptionInWatts']  # current grid power consumption in Watts
        loadPower = instantEGaugeData['TotalPowerConsumptionInWatts']  # Total loads current consumption in Watts
        solarPower = instantEGaugeData['SolarPowerGenerationInWatts'] # current generation in Watts

        #logger.debug(instantEGaugeData)
        #logger.info("It's Data!   loadPower: %s    gridPower: %s     solarPower: %s", loadPower, gridPower, solarPower)

    #    data['GridEnergyConsumptionInWattSeconds']  # grid-powered daily energy in Watt-seconds
    #    data['TotalEnergyConsumptionInWattSeconds']  # Total loads daily energy in Watt-seconds
    #    data['SolarEnergyGenerationInWattSeconds'] # daily energy generated in Watt-seconds


        # Use Influx line protocol for now, it has the format:
        #    measurement,tag_set field_set timestamp
        # https://docs.influxdata.com/influxdb/v1.7/write_protocols/line_protocol_tutorial/

        influx_line = "power,equipment_id=egauge30808 power_solar={},power_grid={},power_load={}".format(
            solarPower,
            gridPower,
            loadPower)
        logger.debug(influx_line)

#        dbClient.write(influx_line, protocol='line')
        result = dbClient.write([influx_line],{'db':INFLUX_DB},protocol='line')

#        try:
            # publish values to MQTT broker
#            myMQTT.publish(MQTT_TOPIC_EGAUGE, influx_line)

#        except Exception as e:
#            logger.error("Error publishing to MQTT: %s", e)

        # Sleep a total 5 seconds between iterations
        time.sleep(6)

    # end while "True"
