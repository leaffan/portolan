#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File: get_drafted_players.py
# Author: Markus Reinhold
# Contact: leaffan@gmx.net
# Creation Date: 2016/11/25 14:32:29

"""
Retrieve all players drafted in an NHL Entry Draft from eliteprospects.com. As
a result a dictionary using the birthdate as key and a list of players born on
this date as values. Later on this dictionary can be used to determine whether
a player has already been drafted.
"""
import os
import json
from urllib.parse import urlparse
from collections import defaultdict

import requests

from lxml import html

# base url for eliteprospects.com
BASE_URL = "http://www.eliteprospects.com"
# url template for draft overview pages at eliteprospects.com
DRAFT_URL_TEMPLATE = "draft/nhl-entry-draft/%d"
# default target data file
TGT_FILE = "drafted_players_by_dobs.json"



def retrieve_drafted_player_links(draft_year):
    """
    Retrieves links to player pages for all players drafted in the specified
    draft year.
    """
    url = "/".join((BASE_URL, DRAFT_URL_TEMPLATE % draft_year))
    req = requests.get(url)
    doc = html.fromstring(req.text)

    # full links to player pages are present at the specified position in
    # the main table
    return doc.xpath(
        "//table[@data-sort-ajax-container='#drafted-players']/tbody/" +
        "tr/td[@class='player']/span/a/@href")


def retrieve_drafted_player_data(player_links, existing_player_data=None):
    """
    Retrieves basic player data (full name, date of birth) from all player
    pages in the specified list.
    """
    # setting up target dictionary using an empty list as a default value
    # because multiple players may be born on the same day
    if existing_player_data is None:
        player_dobs = defaultdict(list)
    else:
        player_dobs = existing_player_data

    i = 0
    for url in player_links[:]:
        i += 1
        req = requests.get(url)
        print("+ Working on url %d of %d (%s)" % (i, len(player_links), url))
        doc = html.fromstring(req.text)

        # retrieving full name from page title
        full_name = doc.xpath(
            "//title/text()").pop().replace('- Elite Prospects', '').strip()

        # retrieving date of birth
        dob_url = doc.xpath("//a[contains(@href, '?dob=')]/@href").pop()
        url_comps = urlparse(dob_url)
        for item in url_comps.query.split('&'):
            if 'dob' in item:
                dob = item.split("=")[-1]

        # adding current player to dictionary of player using his date of birth
        # as key
        # temporarily convert list to set in order to avoid duplicate entries
        dob_players = set(player_dobs[dob])
        dob_players.add(full_name)
        # re-converting set to list to make 
        player_dobs[dob] = list(dob_players)

    return player_dobs


if __name__ == '__main__':

    if os.path.isfile(TGT_FILE):
        all_plr_dobs = json.loads(open(TGT_FILE).read())
    else:
        all_plr_dobs = defaultdict(list)

    for year in [2014, 2015, 2016, 2017, 2018]:
        print("+ Retrieving all players drafted in %d" % year)
        plr_links = retrieve_drafted_player_links(year)
        all_plr_dobs = retrieve_drafted_player_data(plr_links, all_plr_dobs)

    open(TGT_FILE, 'w').write(
        json.dumps(all_plr_dobs, indent=2, sort_keys=True))
