import re
from collections import OrderedDict
from typing import Dict, Union, List
import csv, json

watch_words = [ # order matters in regex!
    'allow',
    'permissive',
    'guarantee',
    'prohibit',
    'permit',
    # 'permitt',
    # 'exempt',
    'restrictive',
    'regulate',
    'require',
    'oblige',
    'protect',
    'sign',
    'provide',
    'designate'
    'donate',
    'declare',
    'list',
    'license',
    'submit',
    'join',
    'signed and ratified',
    'ratified',
    'signed'
               ]

negate_words = {' not ', ' no '}
# number of char leeway between a "not" and the categorical word
negate_dist = 20

re_ww = (
        "((?P<negate>{})(.".format('|'.join( ('(' + nw + ')' for nw in negate_words) ))
        + "{"
        + "0,{}".format(negate_dist)
        + "}"
        + "?))?(?P<value>{})".format('|'.join( ('(' + ww + ')' for ww in watch_words) ))
         )


# TODO: Capture denominator of rates? (Though it seems most are described in label)
regex_dict = OrderedDict(
    {
        # match "2013: 30505", etc.
    'time_series': r'(?P<year>\d+):\ * (?P<value>[\d|\%|\.|,]+)',
        # match "235258 to 5035030", etc.
    'range':r'\$?(?P<low>[\d|\.|,]+)\ +(to)?[\ |\$]*(?P<high>[\d|\.|,]+)',
        # match "was permitted", "was not permitted", etc.
        # negation word caught in separate `negate` key
    'categorical': r'{}'.format(re_ww),
        # match "the total number was 306501 (2013)", etc.
    'single_value': r'\$?(?P<value>\d[\d|,|\.]+)\s*(\((?P<time>\d+)\))?'
    }
)

for (k,v) in regex_dict.items():
    try:
        regex_dict[k] = re.compile(v)
    except:
        pass


#### Helper Functions

def _try_cast_number(s: str) -> Union[int, float, str]:
    try:
        s = ''.join((ch for ch in s if ch != ','))
    except TypeError:  # probably "None"
        return s

    # deal with empty/weird cases
    if not s:
        return s

    # deal with percentages; convert to floats
    if s[-1] == '%':
        try:
            return float(s[:-1])/100
        except ValueError: # !? Adversarial, unnatural writing
            ...

    # def ident(s):
    #     return s

    for f in (int, float):
        try:
            return f(s)
        except ValueError:
            pass

    return s


# categorical_dict = {'firearm_regulation_-_guiding_policy': None}
# time_series_list = ['rate_of_unintentional_male_gun_death_per_100_000_people']


## Content cleaner
#
# TODO: Set up Item Pipeline instead of doing cleaning here?
def clean_dict(datum_dict: Dict[str, Dict]) -> Dict[str, Dict]:
    '''Clean up "content" entry according to "id".

    We see whether it "looks like" in the following order (type(value) in paren):
    (1) time-series data (dict: int(year)->float/int)
    (2) range (dict: "low/high"->float/int)
    (3) categorical (dict: "value" -> str)
    (4) single number (dict: "value"(+"time") -> float/int)


    Input Dict's Keys/Values:
    =====
    id: a string
    content: an XML-path which, if you call .getall() on it, returns a list of strings

    Returns:
    =======
    Dictionary with pairs:
    id -> str
    content -> Dict // parsed content. If nonempty, includes key "type", describing feature (which regex it matched)
    '''
    list_content, id = datum_dict['content'].css("::text").getall(), datum_dict['id']

    # cleanup of list_content
    # we assume lines with just a single number are citation numbers and so drop them
    list_content = [e for e in list_content if e is not '' and not e.isdigit()]

    str_content = ' '.join(list_content)
    # res_dict = {id: {}}
    dict_temp = {}
    dict_clean = {}
    dict_out = {'id': id}

    if id == 'right_to_possess_firearms':
        print("hi")

    for (label, matcher) in regex_dict.items():
        try:
            matched = list(matcher.finditer(str_content)) # list(finditer) to have re.Match objects
            assert len(matched) > 0
            # also remember "type" of value
            dict_temp['type'] = label

            if len(matched) == 1:
                dict_temp.update(matched[0].groupdict())
            else: # time-series or pathological
                if label != 'time_series':
                    dict_temp.update(matched[0].groupdict()) # we'll just take the first one for now
                    break
                for m in matched:
                    try:
                        d = m.groupdict()
                        year = d['year']
                        value = d['value']
                        dict_temp[year] = value
                    except KeyError:
                        ... # TODO: Do we need to do something here?
            break
        except (AttributeError, AssertionError):
            continue

    # cast strings to ints/floats
    for (k,v) in dict_temp.items():
        k = _try_cast_number(k)
        v = _try_cast_number(v)
        dict_clean[k] = v

    dict_out['content'] = dict_clean
    return dict_out
    # return {'id': id, 'content': dict_clean}



def post_process_json(json_fp: str) -> None:
    """
    Given path to the output JSON of crawler,
    postprocess the JSON to be "tidified".

    :return: a List of dictionaries, one per country
    """
    MISSING_VALUE = -42

    with open(json_fp) as f:
        list_json = json.load(f)


    def tidify_list_entries(d: Dict[str, List], prefix: str) -> Dict:
        d_tidy = {}
        for (inner_key, value) in values_dict.items():
            tidy_key = "{}_{}".format(prefix, inner_key)
            d_tidy[tidy_key] = value
        return d_tidy

    # we convert the list_json into a list of "tidified" dicts

    list_tidy = []

    # to fix incorrect matches
    vals_to_type = {str: 'categorical', int: 'single_value', float: 'single_value'}

    while list_json:
        dd_country = list_json.pop()

        for country, d_info in dd_country.items(): # single-key dd
            d_tidy = {'country': country}
            for key, values_dict in d_info.items():
                if not values_dict: # empty for this country
                    # d_tidy[key] = MISSING_VALUE
                    continue

                values_dict = {d:k for (d,k) in values_dict.items() if k is not None}
                cur_type = values_dict.pop('type')

                if cur_type in ['time_series', 'range']:  # build keyname
                    # first, remove possible mistakes by earlier scraper
                    values_dict = {k:v for (k,v) in values_dict.items() if type(v) is int or type(v) is float}

                    # was it a range that now only has one end?
                    if len(values_dict) == 1 and ('high' in values_dict or 'low' in values_dict):
                        # oops.. recast as relevant type
                        values_dict['value'] = list(values_dict.values())[0]
                        cur_type = vals_to_type[type(values_dict['value'])]
                    else:
                        d_tidy.update(tidify_list_entries(values_dict, prefix=key))
                if cur_type in {'categorical'}:
                    val = int(bool(values_dict['value']))- int(values_dict.get('negate', None) is not None)
                    d_tidy[key] = val
                if cur_type in {'single_value'}:
                    try:
                        tidy_key = "{}_{}".format(key, values_dict['time'])
                        d_tidy[tidy_key] = values_dict['value']
                    except KeyError:
                        d_tidy[key] = values_dict['value']

        list_tidy.append(d_tidy)

    # we'll maintain the same order as JSON
    return list(reversed(list_tidy))





def json_to_csv(json: List, outp: str, index: str=None) -> None:
    '''
    Takes a JSON (list) and outputs a matching CSV at outp.
    If index is specified, tries to bring that row as first row. (Exception if non-existent.)
    Rest of keys are indexed alphabetically.
    '''
    # keys = list(max(json, key=lambda x: len(x)).keys())
    keys = set()
    for d in json:
        keys.update(d.keys())
    # keys = reduce(lambda x,y: x.update(y), (d.keys() for d in json))
    keys = sorted(list(keys))

    try:
        keys.remove(index)
        keys = [index] + keys
    except ValueError:
        pass

    with open(outp, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(json)

    return


# json_to_csv(post_process_json('res.json'), outp='res.csv', index='country')