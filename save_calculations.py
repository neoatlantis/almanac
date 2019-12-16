#!/usr/bin/env python3

import yaml 
import os


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


def getCached(name, year):
    path = os.path.join("calculations-cache", "%s-%d.yaml" % (name, year))
    data = yaml.load(open(path, "r").read())
    return data

def _getCachedResult(name, year, calcfunc):
    # Checks if calcfunc had run before. If yes, return cached value.
    # Otherwise, run calcfunc, cache its result, and return that.
    path = os.path.join("calculations-cache", "%s-%d.yaml" % (name, year))
    if os.path.isfile(path):
        try:
            print("Cache %s(%d) found." % (name, year))
            data = yaml.load(open(path, "r").read())
            return data
        except:
            print("Cache %s(%d) corrupted. Calculate for that." % (name,year))
    data = calcfunc(year=year)
    open(path, "w+").write(yaml.dump(data, default_flow_style=False))
    return data


def cached(name, year):
    # Use @cached('solarterms', 2020) to decorate the calculation function
    # for solar terms. The `year` argument will be passed to this calculation
    # function.
    def wrapper(calcfunc):
        return lambda: _getCachedResult(name, year, calcfunc)
    return wrapper

