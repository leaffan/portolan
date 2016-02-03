#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""
A Python class representing an NHL division.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import MetaData
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import or_, and_
from sqlalchemy.sql.expression import func

db_engine = 'postgresql'
user = '***'
password = '***'
host = '***'
port = '5432'
database = '***'

conn_string = "%s://%s:%s@%s:%s/%s" % (db_engine, user, password, host, port, database)

Engine = create_engine(conn_string, echo = False, pool_size = 5)
Session = sessionmaker(bind = Engine)
Base = declarative_base(metadata = MetaData(schema = 'nhl_db', bind = Engine))

from nhl_team import NHLTeam

class NHLDivision(Base):
    u"""A class representing an NHL division.
    
    Associated table: 'nhl_divisions'
    """
    __tablename__ = 'nhl_divisions'
    __autoload__ = True

    def __init__(self, name, season, teams, conference = None):
        self.division_name = name
        self.year = season
        self.teams = list()
        for t in teams:
            self.teams.append(t.team_id)
        self.conference = conference

    @classmethod
    def get_divisions_and_teams(cls, year):
        session = Session()
        divs = session.query(NHLDivision).filter(
            NHLDivision.year == year).all()
        for d in divs:
            teams = list()
            for team_id in d.teams:
                team = NHLTeam.find_by_id(team_id)
                teams.append(team)
            print d.division_name
            for t in teams:
                print "\t", t
                
def create_divisions(division_src_file):
    lines = open(division_src_file).readlines()
    
    session = Session()
    try:
        for line in lines:
            if line.startswith("#"):
                continue
            division_name, season, teams, conference = line.strip().split(";")
            season = int(season)
            team_abbrs = teams[1:-1].split(',')
            teams = list()
            for t in team_abbrs:
                team = NHLTeam.find(t)
                teams.append(team)
            else:
                if conference:
                    division = NHLDivision(division_name, season, teams, conference)
                else:
                    division = NHLDivision(division_name, season, teams)
                session.add(division)
                
                ids = "{" + ",".join([str(t.team_id) for t in teams])  + "}"
                if conference:
                    output = "%s Division (%s Conference):\t%d\t%s" % (division_name, conference, season, ids)
                else:
                    output = "%s Division:\t%d\t%s" % (division_name, season, ids)
                print output
        else:
            session.commit()
    except:
        session.rollback()
            
            
if __name__ == '__main__':
    
    division_src_file = r"nhl_division_config.txt"
    
    create_divisions(division_src_file)
    
    NHLDivision.get_divisions_and_teams(2006)
