import logging
import re
from typing import List, Tuple
import pickle
import os

from model.model_base import Outcome
from model.model_verification import VerifyStatus
from model.model_code import SectionType
from myutils import *

from config import MAX_HEXDUMP_SIZE

EXT_INFO = ".outcome"
EXT_LOG = ".log"


def getOutcomesFromDir(dir: str) -> List[Outcome]:
    outcomes = []

    filepaths = get_filepaths(dir, EXT_INFO)
    for filepath in sorted(filepaths):
        filepath = filepath[:-len(EXT_INFO)]
        outcome, _, errStr = getFileData(filepath)
        if errStr is not None:
            logging.error("Err parsing file: {} {}".format(filepath, errStr))
            continue
        outcomes.append(outcome)
    return outcomes


def OutcomesToCsv(outcomes: List[Outcome]):
    matchSectionKeys = []
    csvHeader = "name;ident;size;scanDuration;chunksTested;matchesAdded;appraisal;Cnt;CntDom;CntCode;CntData"

    lines = []
    for outcome in outcomes:
        ret  = ''
        if not outcome.isScanned:
            continue

        cntDom = 0
        cntCode = 0
        cntData = 0
        matchSections = {}
        if outcome.verification:
            for verifyStatus in outcome.verification.matchConclusions.verifyStatus:
                if verifyStatus is not VerifyStatus.IRRELEVANT:
                    cntDom += 1

            for match in outcome.matches:
                if match.sectionType is SectionType.CODE:
                    cntCode += 1
                if match.sectionType is SectionType.DATA:
                    cntData += 1

                if match.section is None:
                    n = 'unknown'
                else:
                    n = match.section.name
                if n in matchSections:
                    matchSections[n] += 1
                else:
                    matchSections[n] = 1

                if n not in matchSectionKeys:
                    matchSectionKeys.append(n)

        ret += "{};{};{};{};{};{};{};{};{};{};{}".format(
            outcome.fileInfo.name,
            outcome.fileInfo.ident,
            outcome.fileInfo.size,

            outcome.scanInfo.scanDuration,
            outcome.scanInfo.chunksTested,
            outcome.scanInfo.matchesAdded,

            outcome.appraisal.name,
            len(outcome.matches),
            cntDom,
            cntCode,
            cntData,
        )

        #if outcome.verification:
        #    for verifyStatus in outcome.verification.matchConclusions.verifyStatus:
        #        ret += ";{}".format(verifyStatus.name)
        lines.append({
            "line": ret,
            "sections": matchSections
        })

    matchSectionKeys = sorted(matchSectionKeys)

    ret = ''
    ret += csvHeader
    for k in matchSectionKeys:
        ret += ";{}".format(k)
    ret += "\r\n"

    for entry in lines:
        a = ''
        for k in matchSectionKeys:
            if k in entry["sections"]:
                a += ";{}".format(entry["sections"][k])
            else:
                a += ";0"

        ret += entry["line"] + a + "\r\n"


    return ret


def get_filepaths(folder, ext) -> List[str]:
    filenames = [f for f in os.listdir(folder) if f.endswith(ext)]
    return [os.path.join(folder, f) for f in filenames]


def getFileData(filepath) -> Tuple[Outcome, str, str]:
    verifyDataFile = filepath + EXT_INFO
    logFilename = filepath + EXT_LOG

    outcome: Outcome = None
    logData: str = None

    # Main file (exe, docx etc.)
    if not os.path.isfile(filepath):
        logging.error("File does not exist: " + filepath)
        return None, None, 'File not found: ' + filepath

    # log file
    logData = ""
    if os.path.isfile(logFilename):
        with open(logFilename) as f:
            logData = f.read()
    else:
        return None, None, 'File not found: ' + logFilename

    # Outcome
    outcome: Outcome = None
    if os.path.isfile(verifyDataFile):
        with open(verifyDataFile, "rb") as input_file:
            outcome = pickle.load(input_file)
    else:
        return None, None, 'File not found: ' + verifyDataFile

    return outcome, logData, None


def hexdmp(src, offset=0, length=16):
    if len(src) > MAX_HEXDUMP_SIZE:
        return "Match too large ({} > {} max, do not show".format(len(src), MAX_HEXDUMP_SIZE)

    result = []
    digits = 4 if isinstance(src, str) else 2
    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["%0*X" % (digits, x)  for x in s])
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.'  for x in s])
        result.append("%08X   %-*s   %s" % (i+offset, length*(digits + 1), hexa, text) )
    return('\n'.join(result))


def hexstr(src: bytes, offset=0, length=0):
    if length == 0:
        length = len(src)
    byte_buffer = src[offset:offset+length]
    hex_string = ' '.join([f'{x:02x}' for x in byte_buffer])
    return hex_string


# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
def removeAnsi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)
