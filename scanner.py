import logging
from dataclasses import dataclass
import requests as req
from pprint import pprint



@dataclass
class Scanner:
    scanner_path: str = ""
    scanner_name: str = ""

    def scan(self, data, filename):
        return False


class ScannerTest(Scanner):
    def __init__(self, detections):
        self.detections = detections
        pprint(detections, indent=4)

    def scan(self, data, filename):
        for detection in self.detections:
            fileData = data[detection.refPos:detection.refPos+len(detection.refData)] 
            if fileData != detection.refData:
                return False

        return True    


class ScannerTestWeighted(Scanner):
    def __init__(self, detections):
        self.detections = detections
        pprint(detections, indent=4)

    def scan(self, data, filename):
        n = 0
        for detection in self.detections:
            fileData = data[detection.refPos:detection.refPos+len(detection.refData)] 
            if fileData == detection.refData:
                n += 1

        if n > int(len(self.detections) // 2):
            return True
        else:
            return False


class ScannerRest(Scanner):
    def __init__(self, url, name):
        self.scanner_path = url
        self.scanner_name = name

    def scan(self, data, filename):
        params = { 'filename': filename }
        res = req.post(f"{self.scanner_path}/scan?method=run", params=params, data=data)
        jsonRes = res.json()

        if res.status_code != 200:
            print("Err: " + str(res.status_code))
            print("Err: " + str(res.text))
        
        ret_value = jsonRes['detected']
        return ret_value
