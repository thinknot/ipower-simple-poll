import requests

class egaugeClient(object):

    def _url(path):
        return 'https://10.0.0.47/cgi-bin/' + path


    def get_instant():
        return requests.get(_url('egauge?inst&tot'))
        pass


    def get_history(timespan, interval):
        return requests.get(_url('egauge-show'))
        pass


    def get_team_status():
        return requests.get(_url('egauge?teamstat'))
        pass

