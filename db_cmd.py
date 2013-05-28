#!/usr/bin/python

###################################################################################
# Copyright (c) 2013, Wictor Lund. All rights reserved.                           #
# Copyright (c) 2013, Åbo Akademi University. All rights reserved.                #
#                                                                                 #
# Redistribution and use in source and binary forms, with or without              #
# modification, are permitted provided that the following conditions are met:     #
#      * Redistributions of source code must retain the above copyright           #
#        notice, this list of conditions and the following disclaimer.            #
#      * Redistributions in binary form must reproduce the above copyright        #
#        notice, this list of conditions and the following disclaimer in the      #
#        documentation and/or other materials provided with the distribution.     #
#      * Neither the name of the Åbo Akademi University nor the                   #
#        names of its contributors may be used to endorse or promote products     #
#        derived from this software without specific prior written permission.    #
#                                                                                 #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND #
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED   #
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE          #
# DISCLAIMED. IN NO EVENT SHALL ÅBO AKADEMI UNIVERSITY BE LIABLE FOR ANY          #
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES      #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;    #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND     #
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT      #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS   #
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.                    #
###################################################################################

def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-a', nargs=1, default=["list"], choices=["list", "show", "export"], help="Action to perform")
    parser.add_argument('-e', nargs=1, default=[""], type=str)
    parser.add_argument('-o', nargs=1, default=["db_time_series.csv"], type=str)
    parser.add_argument('-f', nargs=1, default=[None], type=str, help="Database file to operate on.", required=True)
    args = parser.parse_args()
    return {'db_filename'     : args.f[0],
            'action'          : args.a[0],
            'experiment_id'   : args.e[0],
            'output_filename' : args.o[0]} 

def main():
    config = parse_arguments()
                        
    from sqlalchemy import create_engine
    from sqlalchemy import Column, Table, MetaData
    from sqlalchemy import String, Integer, Float
    from sqlalchemy.orm import sessionmaker, mapper
    from sqlalchemy.ext.declarative import declarative_base
    from time import sleep
    from stat_reader import StatReader
    from pprint import PrettyPrinter

    engine   = create_engine('sqlite:///' + config['db_filename'])
    metadata = MetaData(bind=engine)
    session  = sessionmaker(bind=engine)()
    Base     = declarative_base(engine)

    class ExperimentInfo(Base):
        __tablename__ = 'experiment_info'
        __table_args__ = { 'autoload':True }

    class ExperimentData(Base): 
        __tablename__ = 'experiment_data'
        __table_args__ = { 'autoload':True }
    
    pp = PrettyPrinter(indent=2)

    def list_experiments():

        print "Experiment id".rjust(36), "Scheduler".rjust(12), "Target load level".rjust(20), "Start time".rjust(28), "End time".rjust(28)
        
        for r in session.query(ExperimentInfo):
            experiment_id_str = str(r.experiment_id).rjust(36)
            scheduler_str = str(r.scheduler).rjust(12)
            target_load_level_str = str(r.target_load_level).rjust(20)
            start_time_str = str(r.start_time).rjust(28)
            end_time_str = str(r.end_time).rjust(28)
            print experiment_id_str, scheduler_str, target_load_level_str, start_time_str, end_time_str

    def show_experiement_props():
        r = session.query(ExperimentInfo).filter_by(experiment_id = config['experiment_id']).first()

        if r == None:
            print "Could not show info about experiment with id \"%s\"" % config['experiment_id']
            return

        column_names = map(lambda c: str(c).split(".")[1], ExperimentInfo.__table__.columns)
        
        max_col_len = reduce(lambda k, v: max(k, len(v)), column_names, 0)

        for c in column_names:
            print c.rjust(max_col_len + 1), getattr(r, c, "")

    def export_time_series():
        q = session.query(ExperimentData).filter_by(experiment_id = config['experiment_id'])

        if q.count == 0:
            print "Could not find any non-empty time series with experiement id \"%s\"" % config['experiment_id']
            return

        with open(config['output_filename'], "wb") as f:
            print "Exporting data in csv format to file \"%s\"..." % config['output_filename']
            from csv import writer as csvwriter
            w = csvwriter(f, delimiter=",")
            i = 0
            for r in q:
                w.writerow([r.time, r.voltage, r.current, r.power, r.temperature])
                i += 1
        print "Exported %i samples." % i
        print "Row order: time, voltage, current, power, temperature"

    if config["action"] == "list":
        list_experiments()
    elif config["action"] == "show":
        show_experiement_props()
    elif config["action"] == "export":
        export_time_series()

if __name__ == '__main__':
    main()
