# gapps_converted.py
# A Python translation (helpers) of many server-side functions from your original code.gs.

from datetime import datetime

def normalize_percent_value(val):
    if val is None:
        return ''
    s = str(val).strip()
    if s == '' or s == '-':
        return ''
    # remove percent sign and convert to 0..1 decimal string
    if s.endswith('%'):
        s = s[:-1]
    try:
        num = float(s)
        if num > 1:
            return str(num/100)
        return str(num)
    except:
        return ''

def is_flour_ingredient(name):
    keywords = ['高筋麵粉','中筋麵粉','低筋麵粉','全麥麵粉','裸麥粉','麵粉']
    return any(k in (name or '') for k in keywords)

def is_percentage_group(group):
    groups = ['主麵團','麵團餡料A','麵團餡料B','波蘭種','液種','中種','魯班種']
    return group in groups

# You can import more helper translations from the original code.gs as needed.
