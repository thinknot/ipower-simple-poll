from datetime import datetime
from lxml import etree


class EgaugeData(object):

    def __init__(self, xml_string):
        self.config_serial_number = None
        self.num_registers = 0
        self.regname = []
        self.regtype = []
        self.ts = []
        self.row = []

        xml = etree.fromstring(xml_string)
        if xml.tag != 'group':
            raise Exception('Expected <group> as the top element')
        self.config_serial_number = int(xml.attrib['serial'], 0)

        for data in xml:
            ts = None
            delta = None
            if data.tag != 'data':
                raise Exception('Expected <data> elements within <group>')

            # timestamp - specifies the UNIX timestamp (in hex) for the first row.
            # timedelta - specifies the number of seconds to be subtracted to get the next row’s timestamp.
            # epoch - specifies the UNIX timestamp (in hex) of the time at which recording started.
            # delta - equal to 'true' if the data rows are delta-encoded
            if 'columns' in data.attrib:
                self.num_registers = int(data.attrib['columns'])
            if 'time_stamp' in data.attrib:
                ts = int(data.attrib['time_stamp'], 0)
            if 'time_delta' in data.attrib:
                delta = int(data.attrib['time_delta'], 0)
            if 'epoch' in data.attrib:
                self.epoch = int(data.attrib['epoch'], 0)

            if ts is None:
                raise Exception('<data> element is missing time_stamp attribute')
            if delta is None:
                raise Exception('<data> element is missing time_delta attribute')

            for el in data:
                if el.tag == 'r':
                    row = []
                    for c in el:
                        row.append(int(c.text))
                    self.ts.append(ts)
                    self.row.append(row)
                    ts -= delta
                elif el.tag == 'cname':
                    t = "P"
                    if 't' in el.attrib:
                        t = el.attrib['t']
                    self.regname.append(el.text)
                    self.regtype.append(t)
        return

    def __str__(self):
        ret = ""
        ret += "serial # = %d, " % self.config_serial_number
        ret += "names = %s, " % self.regname
        ret += "types = %s, rows=[" % self.regtype
        for i in range(len(self.ts)):
            if i > 0:
                ret += ", "
            ret += "0x%08x, " % self.ts[i]
            ret += "%s" % self.row[i]
        ret += "]"
        return ret

    def convert(self):
        res = {}
#        res['datasource'] = "%s.%d" % (dev_id,
#                                       self.config_serial_number)
        catalog = []
        for regnum in range(len(self.regname)):
            meter = {}
            meter['meterId'] = regnum
            meter['meterName'] = self.regname[regnum]
            meter['meterUnits'] = 'Wh'
            catalog.append(meter)
        res['metercatalog'] = catalog
        prev_ts = None
        prev_row = None

        readings = []
        for i in range(len(self.ts)):
            ts = self.ts[i]
            row = self.row[i]
            if prev_ts and prev_row:
#                ts_str = datetime.fromtimestamp(ts).isoformat()
                for regnum in range(len(self.row[i])):
                    reading = {}
                    if self.regtype[regnum] != 'P':
                        continue
                    val = (row[regnum] - prev_row[regnum]) # the magic, the change
                    reading['timestamp'] = ts # eGauge timestamps are UTC...
                    reading['value'] = abs(val / 3600.0)  # convert to Wh
                    reading['meterId'] = regnum
                    readings.append(reading)
            prev_ts = ts
            prev_row = row

        res['readings'] = readings
        return res