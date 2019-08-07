#!/usr/bin/env python3

class CalculationResults:

    def __init__(self, name, year, filetype="tex"):
        self.path = "calculations/%d/%s.%s" % (year, name, filetype)

    def writeline(self, line):
        self.file.write(line)
        self.file.write("\n")

    def __enter__(self, *args, **kvargs):
        self.file = open(self.path, "w+")
        return self

    def __exit__(self, *args, **kvargs):
        self.file.close()
