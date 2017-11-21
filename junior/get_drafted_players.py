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
import json
from urllib.parse import urlparse
from collections import defaultdict, namedtuple

import requests

from lxml import html

# base url for eliteprospects.com
BASE_URL = "http://www.eliteprospects.com"
# url template for draft overview pages at eliteprospects.com
DRAFT_URL_TEMPLATE = "draft.php?year=%d"

# named tuple to contain basic player information
Player = namedtuple('Player', 'first_name last_name')


def retrieve_drafted_player_links(draft_year):
    u"""
    Retrieves links to player pages for all players drafted in the specified
    draft year.
    """
    url = "/".join((BASE_URL, DRAFT_URL_TEMPLATE % draft_year))
    req = requests.get(url)
    doc = html.fromstring(req.text)

    # stub links to player pages are present at the specified position in
    # the main table
    return ["/".join((BASE_URL, link)) for link in doc.xpath(
        "//tr[@bordercolor='#FFFFFF']/td[3]/a/@href")]


def retrieve_drafted_player_data(player_links, existing_player_data=None):
    u"""
    Retrieves basic player data (first name, last name, date of birth) from all
    player pages in the specified list.
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

        # retrieving birthdate url that contains all necessary information in
        # granular form, i.e. <a href="birthdate.php?Birthdate=1998-04-19&amp;
        # Firstname=Patrik&amp;Lastname=Laine">1998-04-19</a>
        dob_url = doc.xpath("//a[starts-with(@href, 'birthdate')]/@href")
        if not dob_url:
            continue
        dob_url = dob_url.pop(0)
        # retrieving player information from retrieved url
        dob, first_name, last_name = get_player_details_from_url(dob_url)
        # adding current player to dictionary of player using his date of birth
        # as key
        player_dobs[dob].append(Player(first_name, last_name))

    return player_dobs


def get_player_details_from_url(dob_url):
    u"""
    Gets player details, i.e. first name, last name and date of birth, from
    specifield url.
    """
    # exploding url into its components
    url_comps = urlparse(dob_url)
    # retrieving player details by exploding each part of the url's
    # query component
    dob, first_name, last_name = [
        comp.split("=")[-1] for comp in url_comps.query.split("&")]
    return dob, first_name, last_name


if __name__ == '__main__':

    all_plr_dobs = defaultdict(list)

    for year in [2014, 2015, 2016, 2017]:
        print("+ Retrieving all players drafted in %d" % year)
        plr_links = retrieve_drafted_player_links(year)
        all_plr_dobs = retrieve_drafted_player_data(plr_links, all_plr_dobs)

    open(r"d:\drafted_player_dobs.json", 'w').write(
        json.dumps(all_plr_dobs, indent=2, sort_keys=True))
