#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File: get_draft_eligible_junior_players.py
# Author: Markus Reinhold
# Contact: markus@leaffan.net
# Creation Date: 2016/11/03 01:06:32

u"""
This script retrieves player information and current season statistics for all
draft-eligible players in the three junior leagues QMJHL, OHL and WHL.
Results are stored in a JSON-file for later use in other applications or
environments.
"""

import requests, datetime, json, re

from collections import namedtuple
from dateutil.parser import parse
from types import ListType

# definition of named tuples to hold some data
# team information
Team = namedtuple('Team', 'id name city code')
# player information
Player = namedtuple('Player', 'id first_name last_name team league dob draft_day_age is_overager position height weight shoots url')
# single season player statistics
Statline = namedtuple('Statline', 'id season games_played goals assists points plus_minus penalty_minutes power_play_goals power_play_assists power_play_points short_handed_goals short_handed_assists short_handed_points shots shooting_percentage points_per_game')

# defining dates
# lower date of birth for draft-eligible players, older players do not need to be drafted
LOWER_CUTOFF_DOB = parse("Jan 1, 1997").date()
# regular cutoff date of birth for draft-eligible players, younger ones weren't draft-eligible in the previous draft
REGULAR_CUTOFF_DOB = parse("Sep 15, 1998").date()
# upper cutoff date of birth for draft-eligible players, younger ones are only draft-eligible in the next draft
UPPER_CUTOFF_DOB = parse("Sep 15, 1999").date()
# date of the upcoming draft
DRAFT_DATE = parse("Jun 23, 2017").date()

# league-specific template urls for team overview pages
TEAM_OVERVIEW_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&season_id=184&fmt=json",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id=56&fmt=json",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=teamsbyseason&key=c680916776709578&fmt=json&client_code=whl&season_id=257&lang=en&fmt=json",
}

# league-specific template urls for team roster pages
TEAM_ROSTER_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&season_id=184&team_id=%d&fmt=json",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id=56&team_id=%d&fmt=json",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=roster&key=c680916776709578&fmt=json&client_code=whl&lang=en&season_id=257&team_id=%d&fmt=json",
}

# league-specific template urls for team statistic pages
TEAM_STATS_URLS = {
    'QMJHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=lhjmq&lang=en&season_id=184&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
    'OHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id=56&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
    'WHL': "http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=skaters&key=c680916776709578&fmt=json&client_code=whl&lang=en&season_id=257&team_id=%d&league_code=&fmt=json&sort=active&order_direction=",
}

# league-specific template urls for single player pages
PLAYER_PAGE_URLS = {
    'QMJHL': "http://theqmjhl.ca/players/%s",
    'OHL': "http://www.ontariohockeyleague.com/players/%s",
    'WHL': "http://whl.ca/players/%s",
}

# TODO: allow for retrieval of other seasons
SEASON_CODES = {
    'QMJHL': 184,
    'OHL': 56,
    'WHL': 257
}

# necessary regular expressions patterns for height conversion
FEET_INCH_PATTERN = re.compile("(\d).?\s?(\d+)")
FEET_PATTERN = re.compile("(\d).?")

################################################################################

def retrieve_teams(league):
    u"""
    Retrieves teams for specified league by downloading and evaluating a
    corresponding JSON file.
    """
    print "+ Retrieving %s teams..." % league
    
    # retrieving url to team overview page for specified league
    url = TEAM_OVERVIEW_URLS[league.upper()]
    # setting up container for retrieved teams
    teams = dict()
    # retrieving team overview JSON structure
    r = requests.get(url)
    json_data = r.json()
    json_data_node = json_data['SiteKit']['Teamsbyseason']
    # retrieving team names, ids, cities and codes
    team_names = [item['name'] for item in json_data_node]
    team_ids = [int(item['id']) for item in json_data_node]
    team_cities = [item['city'] for item in json_data_node]
    team_codes = [item['code'] for item in json_data_node]

    # integrating retrieved information components in dictionary of teams
    for team_id, team_name, team_city, team_code in zip(team_ids, team_names, team_cities, team_codes):
        team = Team(team_id, team_name.replace(",", ""), team_city, team_code)
        teams[team_id] = team
            
    return teams

def retrieve_roster(team, league):
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
    r = requests.get(url)
    json_data = r.json()
    json_data_node = json_data['SiteKit']['Roster']
    # iterating over each player in JSON structure
    for plr in json_data_node:
        # skipping staff members (provided in a separate sub-list)
        if type(plr) is ListType:
            continue
        # skipping goalies
        if plr['position'] == 'G':
            continue
        # skipping player if he has already been drafted
        if is_nhl_drafted(plr['draftinfo']):
            continue

        # retrieving player's date of birth
        dob = parse(plr['birthdate']).date()

        # skipping non-draft-eligible players
        if not is_draft_eligible(dob):
            continue

        # calculating draft day age and retrieving overager status
        draft_day_age, is_overager = calculate_draft_day_age(dob)

        # retrieving player plage url
        plr_page_url = PLAYER_PAGE_URLS[league] % plr['id']
        
        # converting player height
        height = convert_height(plr['height'])
        
        # TODO: hometown, country
        
        # setting up player object
        player = Player(plr['id'], plr['first_name'].strip(), plr['last_name'].strip(),
                        team, league, dob, draft_day_age, is_overager,
                        plr['position'], height, plr['weight'], plr['shoots'],
                        plr_page_url)
        
        # adding current player to roster
        roster[plr['id']] = player

    return roster

def retrieve_stats(team, league, roster):
    u"""
    Retrieves statlines for specified team roster and league.
    """
    print "+ Retrieving stats for %s (%s)..." % (team.name, league)

    # retrieving url to team statistics page for specified league and team
    url = TEAM_STATS_URLS[league.upper()] % team.id

    # setting up container for retrieved team statistics
    roster_stats = dict()
    # retrieving team statistics JSON structure
    r = requests.get(url)
    json_data = r.json()
    json_data_node = json_data['SiteKit']['Statviewtype']
    # iterating over each player in JSON structure
    for plr in json_data_node:
        plr_id = plr['player_id']
        # skipping players not available in specified roster, i.e. non-draft-eligible players
        if not plr_id in roster:
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
        
        # setting up statline objects
        statline = Statline(plr['player_id'], "", raw_stat_line['games_played'],
                            raw_stat_line['goals'], raw_stat_line['assists'], raw_stat_line['points'],
                            raw_stat_line['plus_minus'], raw_stat_line['penalty_minutes'],
                            raw_stat_line['power_play_goals'], raw_stat_line['power_play_assists'], raw_stat_line['power_play_points'],
                            raw_stat_line['short_handed_goals'], raw_stat_line['short_handed_assists'], raw_stat_line['short_handed_points'],
                            raw_stat_line['shots'], raw_stat_line['shooting_percentage'], raw_stat_line['points_per_game'])

        # adding current statline to roster stats
        roster_stats[plr_id] = statline
    
    return roster_stats

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
        return float("%d.%02d" % tuple([int(x) for x in feet_inch_match.group(1, 2)]))
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
    draft_day_age = float("%d.%03d" % (draft_day_age / 365, draft_day_age % 365))
    
    return draft_day_age, is_overager

def json_serial(obj):
    u"""
    Custom converter to serialize datetime.dates to JSON structures.
    """
    if isinstance(obj, datetime.date):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable: %s" % type(obj))

def dump_to_json_file(tgt_path, rosters, stats):
    u"""
    Dumps rosters and according stats to a JSON file at the specified
    target location.
    """
    # setting up list of JSON file entries
    json_dump_prep = list()

    for player_id in stats:
        # retrieving player and according statline
        player = rosters[player_id]
        statline = stats[player_id]
        
        # setting singe data item
        data_item = dict()
    
        # adding player information and statistics field by field to data item
        for field in Player._fields:
            data_item[field] = getattr(player, field)
        for field in Statline._fields[1:]:
            data_item[field] = getattr(statline, field)
            
        # adding current data item to list of all data items
        json_dump_prep.append(data_item)

    # inserting current date and time into JSON structure as last modification timestamp
    json_dump_prep.insert(0, {"last_modified": datetime.datetime.now().strftime("%a %b %d %Y, %H:%M CET")})
    # finally dumping contents to JSON file
    open(tgt_path, 'wb').write(json.dumps(json_dump_prep, default = json_serial, indent = 2, sort_keys = True))

################################################################################

if __name__ == '__main__':

    tgt_path = r"junior.json"

    # setting up result containers for rosters and player stats
    full_rosters = dict()
    full_stats = dict()
    
    # doing the following for each league
    for league in ['QMJHL', 'OHL', 'WHL']:
        # retrieving teams in current league
        teams = retrieve_teams(league)
        for team in teams.values()[:]:
            # retrieving roster for current team
            roster = retrieve_roster(team, league)
            # updating container for all rosters
            full_rosters.update(roster)
            # retrieving player statistics for current team
            stats = retrieve_stats(team, league, roster)
            # updating container for all player statistics
            full_stats.update(stats)

    # dumping rosters and stats to JSON file
    dump_to_json_file(tgt_path, full_rosters, full_stats)
