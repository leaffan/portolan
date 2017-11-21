#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File: locations.py
# Author: Markus Reinhold
# Contact: markus@leaffan.net
# Creation Date: 2016/11/23 10:01:04

"""
This script allows for ISO country code retrieval for a number of country,
state, province, or territory abbreviations as well as some special cases used
on the hockey websites utilized for data retrieval.
"""

# special cases found on hockey league websites
SPECIAL_CASES = {
    # countries
    'Finlande': 'Finland',
    'Russie': 'Russia',
    'Republic of Belarus': 'Belarus',
    'Czech Rep.': 'Czech Republic',
    # non-standard abbreviations for Canadian provinces
    'NF': 'NL',
    'ONT': 'ON',
    'Man': 'MB',
    'Sas': 'SK',
    'MAN': 'MB',
    'Ontario': 'ON',
}

# state abbreviations for the US
US_STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming',
}

# province and territory abbreviations in Canada
CANADIAN_PROVINCES_TERRITORIES = {
    'AB': 'Alberta',
    'BC': 'British Columbia',
    'MB': 'Manitoba',
    'NB': 'New Brunswick',
    'NL': 'Newfoundland and Labrador',
    'NT': 'Northwest Territories',
    'NS': 'Nova Scotia',
    'NU': 'Nunavut',
    'ON': 'Ontario',
    'PE': 'Prince Edward Island',
    'QC': 'Quebec',
    'SK': 'Saskatchewan',
    'YT': 'Yukon',
}

# standard country abbreviations
COUNTRY_ABBREVIATIONS = {
    'NED': 'Netherlands',
    'SWE': 'Sweden',
    'UKR': 'Ukraine',
    'HUN': 'Hungary',
    'GER': 'Germany',
    'DEN': 'Denmark',
    'CHN': 'China',
    'FIN': 'Finland',
    'LAT': 'Latvia',
    'RUS': 'Russia',
    'CZE': 'Czech Republic',
    'USA': 'United States',
    'SVK': 'Slovakia',
    'NOR': 'Norway',
    'SUI': 'Switzerland',
    'EST': 'Estonia',
    'BLR': 'Belarus',
}

# look-up dictionary for ISO country codes found relevant for
# hockey player data retrieval
ISO_COUNTRY_CODES = {
    'Belarus': 'by',
    'Canada': 'ca',
    'Switzerland': 'ch',
    'China': 'cn',
    'Czech Republic': 'cz',
    'Germany': 'de',
    'Denmark': 'dk',
    'Finland': 'fi',
    'Hungary': 'hu',
    'Latvia': 'lv',
    'Netherlands': 'nl',
    'Norway': 'no',
    'Russia': 'ru',
    'Sweden': 'se',
    'Slovakia': 'sk',
    'Ukraine': 'ua',
    'United States': 'us',
    'Estonia': 'ee',
    'Belgium': 'be',
    'Suisse': 'ch',
    'Poland': 'pl',
}


def retrieve_iso_country_code(orig_abbr):
    """
    Retrieves ISO country code based on specified input string (representing a
    state, province, territory or country abbreviation or any other location
    related sequence of letters).
    """
    # treating special cases
    if orig_abbr in SPECIAL_CASES:
        orig_abbr = SPECIAL_CASES[orig_abbr]

    if orig_abbr.upper().replace(".", "") in US_STATES:
        full_country = 'United States'
    elif orig_abbr.upper().replace(".", "") in CANADIAN_PROVINCES_TERRITORIES:
        full_country = 'Canada'
    elif orig_abbr.upper() in COUNTRY_ABBREVIATIONS:
        full_country = COUNTRY_ABBREVIATIONS[orig_abbr.upper()]
    else:
        full_country = orig_abbr.strip()

    if full_country in ISO_COUNTRY_CODES:
        return ISO_COUNTRY_CODES[full_country]
    else:
        # TODO: proper logging
        return None


if __name__ == '__main__':
    pass
