#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File: get_draft_eligible_junior_players.py
# Author: Markus Reinhold
# Contact: markus@leaffan.net
# Creation Date: 2016/11/03 01:06:32

u"""
This script retrieves player information and current season statistics for all
draft-eligible players in the three junior leagues QMJHL, OHL and WHL and the
USHL.
Results are stored in a JSON-file for later use in other applications or
environments.
"""
# TODO: propper logging


import datetime
import json
import re
import os

from collections import namedtuple

import Levenshtein
import requests
from dateutil.parser import parse

import locations

# definition of named tuples to hold some data
# team information
Team = namedtuple('Team', 'id name city code team_url')
# player information
Player = namedtuple('Player', 'id first_name last_name team league dob country draft_day_age is_overager position height weight shoots url')
# single season player statistics item
Statline = namedtuple('Statline', 'id season games_played goals assists points plus_minus penalty_minutes power_play_goals power_play_assists power_play_points short_handed_goals short_handed_assists short_handed_points shots shooting_percentage points_per_game')
# single season goalie statistics item
StatlineGoalie = namedtuple('StatlineGoalie', 'id season games_played seconds_played minutes_played shots saves goals_against shutouts goals_against_average save_percentage wins losses ot_losses shootout_games_played shootout_wins shootout_losses')

# defining dates
# lower date of birth for draft-eligible players,
# older players do not need to be drafted
LOWER_CUTOFF_DOB = parse("Jan 1, 1997").date()
# regular cutoff date of birth for draft-eligible players,
# younger ones weren't draft-eligible in the previous draft
REGULAR_CUTOFF_DOB = parse("Sep 15, 1998").date()
# upper cutoff date of birth for draft-eligible players,
# younger ones are only draft-eligible in the next draft
UPPER_CUTOFF_DOB = parse("Sep 15, 1999").date()
# date of the upcoming draft
DRAFT_DATE = parse("Jun 23, 2017").date()

# league-specific template urls for team overview pages
TEAM_OVERVIEW_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&fmt=json",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=ohl&lang=en&fmt=json",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=whl&lang=en&fmt=json",
    'USHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=e828f89b243dc43f&fmt=json&client_code=ushl&lang=en&fmt=json",
}

# league-specific template urls for team roster pages
TEAM_ROSTER_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&season_id=184&team_id=%d&fmt=json",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id=56&team_id=%d&fmt=json",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=whl&lang=en&season_id=257&team_id=%d&fmt=json",
    'USHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=e828f89b243dc43f&fmt=json&client_code=ushl&lang=en&season_id=58&team_id=%d&fmt=json",
}

# league-specific template urls for team statistic pages
TEAM_STATS_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&season_id=184&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id=56&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=whl&lang=en&season_id=257&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
    'USHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=e828f89b243dc43f&fmt=json&client_code=ushl&lang=en&season_id=58&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
}

# league-specific template urls for single player pages
PLAYER_PAGE_URLS = {
    'QMJHL': "http://theqmjhl.ca/players/%s",
    'OHL': "http://www.ontariohockeyleague.com/players/%s",
    'WHL': "http://whl.ca/players/%s",
    'USHL': "http://www.ushl.com/view/#/player?playerId=%s"
}

# league-specific base urls
BASE_URLS = {
    'QMJHL': "http://theqmjhl.ca",
    'OHL': "http://www.ontariohockeyleague.com",
    'WHL': "http://whl.ca",
    'USHL': "http://www.ushl.com",
}

# TODO: allow for retrieval of other seasons
SEASON_CODES = {
    'QMJHL': 184,
    'OHL': 56,
    'WHL': 257,
    'USHL': 58,
}

LEAGUE_KEYS = {
    'QMJHL': 'c680916776709578',
    'OHL': 'c680916776709578',
    'WHL': 'c680916776709578',
    'USHL': 'e828f89b243dc43f',
    'BCHL': 'ca4e9e599d4dae55',
    'AHL': '50c2cd9b5e18e390'
}

LEAGUE_CODES = {
    'QMJHL': 'lhjmq',
    'OHL': 'ohl',
    'WHL': 'whl',
    'USHL': 'ushl',
    'BCHL': 'bchl',
    'AHL': 'ahl'
}

# necessary regular expressions patterns for height conversion
FEET_INCH_PATTERN = re.compile(r'(\d).?\s?(\d+)')
FEET_PATTERN = re.compile(r'(\d).?')

# retrieve players already drafted
DRAFTED_PLAYERS_FILE = "drafted_players_by_dobs.json"

###############################################################################


def retrieve_teams(league):
    u"""
    Retrieves teams for specified league by downloading and evaluating a
    corresponding JSON file.
    """
    print "+ Retrieving %s teams..." % league

    # retrieving url to team overview page for specified league
    url = TEAM_OVERVIEW_URLS[league.upper()]
    # setting up container for retrieved teams
    teams_in_league = dict()
    # retrieving team overview JSON structure
    json_data = fetch_json_data(url)
    json_data_node = json_data['SiteKit']['Teamsbyseason']
    # retrieving team names, ids, cities and codes
    team_names = [item['name'] for item in json_data_node]
    team_ids = [int(item['id']) for item in json_data_node]
    team_cities = [item['city'] for item in json_data_node]
    team_codes = [item['code'] for item in json_data_node]

    # integrating retrieved information components in dictionary of teams
    for team_id, team_name, team_city, team_code in zip(team_ids, team_names, team_cities, team_codes):
            if league == 'USHL':
                team_roster_url = "%s/view/#/roster?team=%d&season=%d&league=1&league_code=USHL" % (BASE_URLS[league], team_id, SEASON_CODES[league])
            else:
                team_roster_url = "%s/roster/%d" % (BASE_URLS[league], team_id)
            teams_in_league[team_id] = Team(team_id,
                                            team_name.replace(",", ""),
                                            team_city,
                                            team_code,
                                            team_roster_url)

    return teams_in_league


def retrieve_roster(team, league, already_drafted=None):
    u"""
    Retrieves rosters for specified team and league by downloading and
    evaluating a corresponding JSON file.
    """
    print "+ Retrieving roster for %s (%s)..." % (team.name, league)

    # retrieving url to team roster page for specified league and team
    url = TEAM_ROSTER_URLS[league.upper()] % team.id
    # setting up container for retrieved roster
    roster = dict()
    # retrieving roster JSON structure
    json_data = fetch_json_data(url)
    # iterating over each player in JSON structure
    for plr in json_data['SiteKit']['Roster']:
        # skipping staff members (provided in a separate sub-list)
        if 'id' not in plr:
            continue

        # adjusting id to include league:
        plr_id = "".join((league, plr['id'])).lower()

        # skipping player if he has already been drafted
        if is_nhl_drafted(plr['draftinfo']):
            continue

        # retrieving player's date of birth
        plr_dob = parse(plr['birthdate']).date()

        # skipping player if he is present in a list of already drafted ones
        if is_nhl_drafted_2(" ".join((plr['first_name'].strip(), plr['last_name'].strip())), plr_dob, already_drafted):
            continue

        # skipping non-draft-eligible players
        if not is_draft_eligible(plr_dob):
            continue

        # calculating draft day age and retrieving overager status
        draft_day_age, is_overager = calculate_draft_day_age(plr_dob)

        # retrieving player plage url
        plr_page_url = PLAYER_PAGE_URLS[league] % plr['id']

        # converting player height
        height = convert_height(plr['height'])

        # retrieving last component of homeplace string
        homeplace_comp = plr['homeplace'].split(",")[-1].strip()
        # converting homeplace string to ISO country code
        country = locations.retrieve_iso_country_code(homeplace_comp)

        if plr['position'] == 'G':
            shoots_catches = plr['catches']
        else:
            shoots_catches = plr['shoots']

        # setting up player object and adding it to roster
        roster[plr_id] = Player(plr_id,
                                plr['first_name'].strip(),
                                plr['last_name'].strip(),
                                team,
                                league,
                                plr_dob,
                                country,
                                draft_day_age,
                                is_overager,
                                plr['position'],
                                height,
                                plr['weight'],
                                shoots_catches,
                                plr_page_url)

    return roster


def retrieve_goalie_stats(team, league, roster):
    u"""
    Retrieves goalie statlines for specified team roster and league.
    """
    print "+ Retrieving goalie stats for %s (%s)..." % (team.name, league)

    # retrieving url to team statistics page for specified league and team
    url = (TEAM_STATS_URLS[league.upper()] % team.id).replace(
        "type=skaters", "type=goalies")

    # setting up container for retrieved team statistics
    goalie_statlines = dict()
    # retrieving team statistics JSON structure
    json_data = fetch_json_data(url)
    # iterating over each player in JSON structure
    for plr in json_data['SiteKit']['Statviewtype']:

        # skipping item if it doesn't represent an actual goalie
        if 'player_id' not in plr:
            continue

        plr_id = "".join((league, plr['player_id'])).lower()
        # skipping players not available in specified roster,
        #  e.g. non-draft-eligible players
        if plr_id not in roster:
            continue

        # skipping players that are not actually goalies
        if roster[plr_id].position != 'G':
            continue

        # setting up dictionary for raw stats
        raw_stat_line = dict()
        # retrieving all relevant stats
        for field in StatlineGoalie._fields[2:]:
            if field in ('goals_against_average', 'save_percentage'):
                if plr[field]:
                    value = float(plr[field])
                else:
                    value = None
            # formatting minutes played using a default format of mmmm:ss
            elif field == 'minutes_played':
                value = "%d:%02d" % (int(plr['seconds_played']) / 60,
                                     int(plr['seconds_played']) % 60)
            else:
                value = int(plr[field])
            raw_stat_line[field] = value

        # setting up statline object and adding it to roster stats
        goalie_statlines[plr_id] = StatlineGoalie(
            plr_id, "",
            raw_stat_line['games_played'],
            raw_stat_line['seconds_played'],
            raw_stat_line['minutes_played'],
            raw_stat_line['shots'],
            raw_stat_line['saves'],
            raw_stat_line['goals_against'],
            raw_stat_line['shutouts'],
            raw_stat_line['goals_against_average'],
            raw_stat_line['save_percentage'],
            raw_stat_line['wins'],
            raw_stat_line['losses'],
            raw_stat_line['ot_losses'],
            raw_stat_line['shootout_games_played'],
            raw_stat_line['shootout_wins'],
            raw_stat_line['shootout_losses'])

    return goalie_statlines


def retrieve_stats(team, league, roster):
    u"""
    Retrieves skater statlines for specified team roster and league.
    """
    print "+ Retrieving skater stats for %s (%s)..." % (team.name, league)

    # retrieving url to team statistics page for specified league and team
    url = TEAM_STATS_URLS[league.upper()] % team.id

    # setting up container for retrieved team statistics
    roster_statlines = dict()
    # retrieving team statistics JSON structure
    json_data = fetch_json_data(url)
    # iterating over each player in JSON structure
    for plr in json_data['SiteKit']['Statviewtype']:
        plr_id = "".join((league, plr['player_id'])).lower()
        # skipping players not available in specified roster,
        # e.g. non-draft-eligible players
        if plr_id not in roster:
            continue

        # setting up dictionary for raw stats
        raw_stat_line = dict()
        # retrieving all relevant stats
        for field in Statline._fields[2:]:
            if field in ('points_per_game', 'shooting_percentage'):
                value = float(plr[field])
            else:
                value = int(plr[field])
            raw_stat_line[field] = value

        # setting up statline objects and adding it to roster stats
        roster_statlines[plr_id] = Statline(plr_id, "",
                                            raw_stat_line['games_played'],
                                            raw_stat_line['goals'],
                                            raw_stat_line['assists'],
                                            raw_stat_line['points'],
                                            raw_stat_line['plus_minus'],
                                            raw_stat_line['penalty_minutes'],
                                            raw_stat_line['power_play_goals'],
                                            raw_stat_line['power_play_assists'],
                                            raw_stat_line['power_play_points'],
                                            raw_stat_line['short_handed_goals'],
                                            raw_stat_line['short_handed_assists'],
                                            raw_stat_line['short_handed_points'],
                                            raw_stat_line['shots'],
                                            raw_stat_line['shooting_percentage'],
                                            raw_stat_line['points_per_game'])

    return roster_statlines


def is_nhl_drafted(draft_info):
    u"""
    Determines whether specified draft information reveals the according
    player as already drafted by an NHL team.
    """
    for item in draft_info:
        if item['draft_type'] == 'NHL' and item['draft_rank']:
            return True
    else:
        return False


def is_nhl_drafted_2(player_name, player_dob, already_drafted_players):
    u"""
    Determines whether specified player name is present in a dictionary of
    already drafted players using the player's date of birth as key comparator.
    """
    if player_dob.isoformat() in already_drafted_players:
        for drafted_player in already_drafted_players[player_dob.isoformat()]:
            drafted_player_name = " ".join(drafted_player)
            levenshtein_ratio = Levenshtein.ratio(
                player_name, drafted_player_name)
            if levenshtein_ratio > 0.8:
                print "-> Already drafted player found: %s vs. %s (Levenshtein ratio: %0.4f)" % (player_name, drafted_player_name, levenshtein_ratio)
                return True
    return False


def is_draft_eligible(player_dob):
    u"""
    Determines whether specified date of birth is a draft-eligible one.
    """
    if player_dob >= LOWER_CUTOFF_DOB and player_dob < UPPER_CUTOFF_DOB:
        return True
    else:
        return False


def convert_height(height):
    u"""
    Converts input height to a sortable height string.
    """
    feet_inch_match = re.match(FEET_INCH_PATTERN, height)
    feet_match = re.match(FEET_PATTERN, height)

    if feet_inch_match:
        return float(
            "%d.%02d" % tuple([int(x) for x in feet_inch_match.group(1, 2)]))
    elif feet_match:
        return float("%d.%02d" % (int(feet_match.group(1)), 0))
    else:
        return None


def calculate_draft_day_age(player_dob):
    u"""
    Calculates age of player on draft day and determines whether player is
    considered an overager.
    """
    if player_dob < REGULAR_CUTOFF_DOB:
        is_overager = True
    else:
        is_overager = False

    draft_day_age = (DRAFT_DATE - player_dob).days
    draft_day_age = float(
        "%d.%03d" % (draft_day_age / 365, draft_day_age % 365))

    return draft_day_age, is_overager


def json_serial(obj):
    u"""
    Custom converter to serialize datetime.dates to JSON structures.
    """
    if isinstance(obj, datetime.date):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable: %s" % type(obj))


def fetch_json_data(json_url):
    u"""
    Fetches JSON data from specified url.
    """
    req = requests.get(json_url)
    return req.json()


def dump_to_json_file(tgt_path, dump_rosters, dump_stats, goalies=False):
    u"""
    Dumps rosters and according stats to a JSON file at the specified
    target location.
    """
    # setting up list of JSON file entries
    json_dump_prep = list()

    for player_id in dump_stats:
        # retrieving player and according statline
        player = dump_rosters[player_id]
        statline = dump_stats[player_id]

        # setting singe data item
        data_item = dict()

        # adding player information and statistics field by field to data item
        for field in Player._fields:
            data_item[field] = getattr(player, field)
        if goalies:
            for field in StatlineGoalie._fields[1:]:
                data_item[field] = getattr(statline, field)
        else:
            for field in Statline._fields[1:]:
                data_item[field] = getattr(statline, field)

        # adding current data item to list of all data items
        json_dump_prep.append(data_item)

    # inserting current date and time into JSON structure
    # as last modification timestamp
    json_dump_prep.insert(0, {
        "last_modified": datetime.datetime.now().strftime(
            "%a %b %d %Y, %H:%M CET")
    })
    # finally dumping contents to JSON file
    open(tgt_path, 'wb').write(
        json.dumps(
            json_dump_prep, default=json_serial, indent=2, sort_keys=True)
    )


if __name__ == '__main__':

    leagues = ['QMJHL', 'OHL', 'WHL', 'USHL']
    skater_tgt_path = r"junior.json"
    goalie_tgt_path = r"junior_goalies.json"

    # setting up result containers for rosters and player stats
    rosters = dict()
    skater_stats = dict()
    goalie_stats = dict()

    if os.path.isfile(DRAFTED_PLAYERS_FILE):
        already_drafted = json.loads(open(DRAFTED_PLAYERS_FILE).read())
        print(
            "+ List of already drafted players loaded from '%s'" % DRAFTED_PLAYERS_FILE)
    else:
        already_drafted = dict()

    # doing the following for each league
    for current_league in leagues[:]:
        # retrieving teams in current league
        teams = retrieve_teams(current_league)
        for current_team in teams.values()[:]:
            # retrieving roster for current team
            team_roster = retrieve_roster(
                current_team, current_league, already_drafted)
            # updating container for all rosters
            rosters.update(team_roster)
            # retrieving player statistics for current team
            team_skater_stats = retrieve_stats(current_team, current_league, team_roster)
            team_goalie_stats = retrieve_goalie_stats(current_team, current_league, team_roster)
            # updating container for all player statistics
            skater_stats.update(team_skater_stats)
            goalie_stats.update(team_goalie_stats)

    # dumping rosters and stats to JSON files
    dump_to_json_file(skater_tgt_path, rosters, skater_stats)
    dump_to_json_file(goalie_tgt_path, rosters, goalie_stats, goalies=True)
