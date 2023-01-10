import csv, os, glob

[TYPE, PERIOD, VALUE] = range(3)

indicators = {}

def readFile(name):
    with open(name) as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            if not i:continue
            country, _type, value = [row[n] for n in (1, 3, 9)]
            if country in indicators:
                indicators[country][_type] = value
            else:
                indicators[country] = {_type:value}
        file.close()
        
#def allFiles(basePath="/home/brebeufhx5website/brebeufhx5website"):
def allFiles(basePath=""):
    return glob.glob(os.path.join(basePath, "*.csv"))
[readFile(path) for path in allFiles()]
countries = list(indicators.keys())