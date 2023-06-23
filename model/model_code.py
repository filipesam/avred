from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Optional
from intervaltree import Interval, IntervalTree
from enum import Enum
import logging


@dataclass
class Section:
    name: str
    addr: int
    size: int
    virtaddr: int
    scan: bool = True


class SectionsBag:
    def __init__(self):
        self.sections: List[Section] = []
        self.sectionsIntervalTree = IntervalTree()


    def addSection(self, section: Section):
        self.sections.append(section)
        interval: Interval = Interval(section.addr, section.addr + section.size, section)
        self.sectionsIntervalTree.add(interval)

    def removeSectionByName(self, sectionName: str):
        new = []
        for section in self.sections:
            if section.name != sectionName:
                new.append(section)
        self.sections = new

    def getSectionByName(self, sectionName: str) -> Section:
        return next((sec for sec in self.sections if sectionName in sec.name ), None)


    def getSectionByAddr(self, address: int) -> Section:
        for section in self.sections:
            if address >= section.addr and address <= section.addr + section.size:
                return section
        return None
    

    def getSectionNameByAddr(self, address: int) -> Section:
        for section in self.sections:
            if address >= section.addr and address <= section.addr + section.size:
                return section.name
        return "<unknown>"
    

    def getSectionsForRange(self, start: int, end: int) -> List[Section]:
        res = self.sectionsIntervalTree.overlap(start, end)
        res = [r[2] for r in res]
        return res
    

    def printSections(self):
        for section in self.sections:
            print(f"Section {section.name}\t  addr: {hex(section.addr)}   size: {section.size} ")


gpRegisters = [ 
    'eax','ebx','ecx','edx','esi','edi',  # make sure we also check 32 bit
    'ebp', 'esp',
    'al','bl','cl','dl',  # and these.. argh
    'ah','bh','ch','dh', # and these.. argh

    'rax','rbx','rcx','rdx','rsi','rdi',
    'r8','r9','r10','r11','r12','r13','r14','r15' 
    'rbp', 'rsp',
    ]
class AsmInstruction():
    def __init__(self, fileOffset, rva, esil, type, disasm, size, rawBytes):
        self.offset = fileOffset  # offset in file
        self.rva = rva
        self.esil = esil
        self.type = type
        self.disasm = disasm
        self.size = size
        self.rawBytes = rawBytes

        # ESIL
        self.esilComponents = esil.split(",") if esil else []

        # Registers touched
        self.esilTouchedRegisters = []
        for a in self.esilComponents:
            if a in gpRegisters:
                self.esilTouchedRegisters.append(a)


    def registersTouch(self, asmInstruction: AsmInstruction):
        return any(element in self.esilTouchedRegisters for element in asmInstruction.esilTouchedRegisters)


    def __str__(self):
        s = "Offset: {}  RVA: {}  type: {}  disasm: {}  size: {}  esil: {}  bytes: {}".format(
            self.offset,
            self.rva,
            self.type,
            self.disasm,
            self.size,
            self.esil,
            self.rawBytes
        )
        return s


class UiDisasmLine():
    def __init__(self, fileOffset, rva, isPart, text, textHtml):
        self.offset = fileOffset  # offset in file
        self.rva = rva  # relative offset (usually created by external disasm tool)
        self.isPart = isPart  # is this part of the data, or supplemental?
        self.text = text  # the actual disassembled data
        self.textHtml = textHtml  # the actual disassembled data, colored

    def __str__(self):
        s = "Offset: {}  RVA: {}  isPart: {}  Text: {}".format(
            self.offset,
            self.rva,
            self.isPart,
            self.text
        )
        return s
    
    
class SectionType(Enum):
    UNKNOWN = 'u'
    CODE = 'c'
    DATA = 'd'