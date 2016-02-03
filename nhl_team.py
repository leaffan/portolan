#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""
A Python class representing an NHL team.
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

class NHLTeam(Base):
    u"""A class representing an NHL team.
    
    Associated table: 'nhl_teams'
    """
    __tablename__ = 'nhl_teams'
    __autoload__ = True

    def __init__(self):
        pass

    @classmethod
    def find(cls, abbr):
        session = Session()
        try:
            t = session.query(NHLTeam).filter(
                    func.lower(NHLTeam.abbr) == abbr.lower()
                ).one()
        except:
            t = None
        finally:
            session.close()
        return t

    @classmethod
    def find_by_id(cls, team_id):
        session = Session()
        try:
            t = session.query(NHLTeam).filter(
                    NHLTeam.team_id == team_id
                ).one()
        except:
            t = None
        finally:
            session.close()
        return t


    def __str__(self):
        return self.name

if __name__ == '__main__':
    t = NHLTeam.find('TOR')
    print "Team with abbreviation '%s': %s" % ('TOR', t)
    t = NHLTeam.find_by_id(12)
    print "Team with id %d: %s" % (12, t)
