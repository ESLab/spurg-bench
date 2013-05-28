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
    parser.add_argument('-a', nargs=1, default=["list"], choices=["list", "list_avgs", "show", "export", "histograms", "list_sq_err", "parameters_in_range", "plot_pairs", "clustring", "top_scores"], help="Action to perform")
    parser.add_argument('-e', nargs=1, default=[""], type=str, help="Experiment id argument")
    parser.add_argument('-o', nargs=1, default=["db_time_series.csv"], type=str, help="Out file, used for export action")
    parser.add_argument('-l', nargs=1, default=[None], type=float, help="Selected load level")
    parser.add_argument('-max', nargs=1, default=[0.0], type=float, help="Upper limit selector for range")
    parser.add_argument('-min', nargs=1, default=[0.0], type=float, help="Lower limit selector for range")
    parser.add_argument('-clusters', nargs=1, default=[2], type=int, help="Number of clusters to create when using kmeans")
    parser.add_argument('-c', nargs=1, default=["energy"], choices=["energy", "power", "time"], help="Column selector")
    parser.add_argument('-v', nargs=1, default=[0.0], type=float, help="Value selector")
    parser.add_argument('-f', nargs=1, default=[None], type=str, help="Database file to operate on", required=True)
    args = parser.parse_args()
    return {'db_filename'     : args.f[0],
            'action'          : args.a[0],
            'experiment_id'   : args.e[0],
            'output_filename' : args.o[0],
            'selected_load'   : args.l[0],
            'selected_column' : args.c[0],
            'max_range'       : args.max[0],
            'min_range'       : args.min[0],
            'value'           : args.v[0],
            'n_clusters'      : args.clusters[0]}

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

    def get_avg_power(exp_id):
        ts = list(session.query(ExperimentData).filter_by(experiment_id = exp_id))
        avg_power = sum(map(lambda r: r.power, ts)) / len(ts)
        return avg_power

    def get_n_cpus(r):
        return {'0': 1,
                '0-1': 2,
                '0-2': 3,
                '0-3': 4}[r.cpus_online.strip()]

    def get_avg_cpus(exp_id):
        ts = list(session.query(ExperimentData).filter_by(experiment_id = exp_id))
        avg_cpus = float(sum(map(get_n_cpus, ts))) / float(len(ts))
        return avg_cpus

    def list_experiments():

        col_names = ['Exp#', 'Experiment id', 'Scheduler', 'Target load level', 'Start time', 'End time']
        col_widths = map(lambda n: len(n), col_names)
        col_widths[1] = 36
        col_widths[4] = 28
        col_widths[5] = 28

        print " ".join(map(lambda n: col_names[n].rjust(col_widths[n]), range(len(col_names))))

        i = 1
        for r in session.query(ExperimentInfo):
            lens = iter(col_widths)
            exp_n_str = ("%i" % i).ljust(next(lens))
            experiment_id_str = str(r.experiment_id).rjust(next(lens))
            scheduler_str = str(r.scheduler).rjust(next(lens))
            target_load_level_str = str(r.target_load_level).rjust(next(lens))
            start_time_str = str(r.start_time).rjust(next(lens))
            end_time_str = str(r.end_time).rjust(next(lens))
            print experiment_id_str, scheduler_str, target_load_level_str, start_time_str, end_time_str
            i += 1

    def list_experiment_avgs():

        print 'Parameters'
        print 'hotplug_in_load_limit'
        print 'hotplug_out_load_limit'
        print 'hotplug_in_sampling_period and hotplug_out_sampling_period'
        print 'up_threshold'
        print 'sched_olord_lb_upper_limit'

        col_names = ['Experiment id', 'Target load level', 'Avg. Power (W)', 'Est. Energy (J)', 'Total time (s)', 'Avg. CPUs (n)', 'Parameters']
        col_widths = map(lambda n: len(n), col_names)
        col_widths[0] = 36
        col_widths[2] = 13

        print " ".join(map(lambda n: col_names[n].rjust(col_widths[n]), range(len(col_names))))

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])

        q = list(q)

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.avg_cpus = get_avg_cpus(r.experiment_id)
            r.energy = r.avg_power * r.total_time

        q.sort(key=lambda r: r.energy)

        i = 1
        for r in q:
            lens = iter(col_widths)
            experiment_id_str = str(r.experiment_id).rjust(next(lens))
            target_load_level_str = str(r.target_load_level).rjust(next(lens))
            avg_power = get_avg_power(r.experiment_id)
            avg_power_str = str(avg_power).ljust(next(lens))
            energy = avg_power * r.total_time
            energy_str = str(energy).ljust(next(lens))
            total_time_str = str(r.total_time).ljust(next(lens))
            avg_cpus_str = str(r.avg_cpus).ljust(next(lens))
            parameters_str = ' '.join(map(str, [r.hotplug_in_load_limit,
                                                r.hotplug_out_load_limit,
                                                r.hotplug_in_sampling_period,
                                                r.hotplug_out_sampling_period,
                                                r.up_threshold,
                                                r.sched_olord_lb_upper_limit])).ljust(next(lens))
            print experiment_id_str, target_load_level_str, avg_power_str, energy_str, total_time_str, avg_cpus_str, parameters_str
            i += 1

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
                w.writerow([r.time, r.voltage, r.current, r.power, r.temperature, r.cpus_online])
                i += 1
        print "Exported %i samples." % i
        print "Row order: time, voltage, current, power, temperature"

    def plot_histograms():
        from matplotlib.pyplot import bar, show, figure, title, xlabel, plot
        from numpy import histogram

        def plot_histogram(x, n):
            hist, bins = histogram(x, bins = n)
            center = (bins[:-1]+bins[1:])/2
            width = 0.7*(bins[1]-bins[0])
            fig = figure()
            bar(center, hist, align = 'center', width = width)
            return fig

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])

        q_query = q
        q = list(q)

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.energy  = r.avg_power * r.total_time

        the_sample = q_query \
            .filter_by(hotplug_in_load_limit=80) \
            .filter_by(hotplug_out_load_limit=10) \
            .filter_by(hotplug_in_sampling_period=10) \
            .filter_by(hotplug_out_sampling_period=10) \
            .filter_by(up_threshold=30) \
            .filter_by(sched_olord_lb_upper_limit=80) \
            .first()

        n = 10

        plot_histogram(map(lambda r: r.avg_power, q), n)
        plot([the_sample.avg_power]*2, [0,1], color='r')
        title("Avg. Power Histogram")
        xlabel("Power/W")

        plot_histogram(map(lambda r: r.energy, q), n)
        plot([the_sample.energy]*2, [0,1], color='r')
        title("Energy Histogram")
        xlabel("Energy/J")

        plot_histogram(map(lambda r: r.total_time, q), n)
        plot([the_sample.total_time]*2, [0,1], color='r')
        title("Total Time Histogram")
        xlabel("Time/s")

        show()

    def list_sort_sq_error():

        print 'Parameters'
        print 'hotplug_in_load_limit'
        print 'hotplug_out_load_limit'
        print 'hotplug_in_sampling_period'
        print 'hotplug_out_sampling_period'
        print 'up_threshold'
        print 'sched_olord_lb_upper_limit'

        col_names = ['Experiment id', 'Target load level', 'Avg. Power (W)', 'Est. Energy (J)', 'Total time (s)', 'Parameters']
        col_widths = map(lambda n: len(n), col_names)
        col_widths[0] = 36
        col_widths[2] = 13

        print " ".join(map(lambda n: col_names[n].rjust(col_widths[n]), range(len(col_names))))

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])
        q = list(q)

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.energy = r.avg_power * r.total_time
            v = {'power': r.avg_power,
                 'energy': r.energy,
                 'time': r.total_time}[config['selected_column']]
            r.sq_error = (config['value'] - v) ** 2

        q.sort(key=lambda r: r.sq_error)

        for r in q:
            lens = iter(col_widths)
            experiment_id_str = str(r.experiment_id).rjust(next(lens))
            target_load_level_str = str(r.target_load_level).rjust(next(lens))
            avg_power = get_avg_power(r.experiment_id)
            avg_power_str = str(avg_power).ljust(next(lens))
            energy = avg_power * r.total_time
            energy_str = str(energy).ljust(next(lens))
            total_time_str = str(r.total_time).ljust(next(lens))
            parameters_str = ' '.join(map(str, [r.hotplug_in_load_limit,
                                                r.hotplug_out_load_limit,
                                                r.hotplug_in_sampling_period,
                                                r.hotplug_out_sampling_period,
                                                r.up_threshold,
                                                r.sched_olord_lb_upper_limit])).ljust(next(lens))
            print experiment_id_str, target_load_level_str, avg_power_str, energy_str, total_time_str, parameters_str

    def list_parameters_in_range():

        print 'Parameters'
        print 'hotplug_in_load_limit'
        print 'hotplug_out_load_limit'
        print 'hotplug_in_sampling_period'
        print 'hotplug_out_sampling_period'
        print 'up_threshold'
        print 'sched_olord_lb_upper_limit'

        col_names = ['Experiment id', 'Target load level', 'Avg. Power (W)', 'Est. Energy (J)', 'Total time (s)', 'Parameters']
        col_widths = map(lambda n: len(n), col_names)
        col_widths[0] = 36
        col_widths[2] = 13

        print " ".join(map(lambda n: col_names[n].rjust(col_widths[n]), range(len(col_names))))

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])
        q = list(q)

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.energy = r.avg_power * r.total_time

        key_fn = {'power': lambda r: r.avg_power,
                  'energy': lambda r: r.energy,
                  'time': lambda r: r.total_time}[config['selected_column']]

        q.sort(key=key_fn)

        q = filter(lambda r: key_fn(r) >= config['min_range'] and key_fn(r) <= config['max_range'], q)

        for r in q:
            lens = iter(col_widths)
            experiment_id_str = str(r.experiment_id).rjust(next(lens))
            target_load_level_str = str(r.target_load_level).rjust(next(lens))
            avg_power = get_avg_power(r.experiment_id)
            avg_power_str = str(avg_power).ljust(next(lens))
            energy = avg_power * r.total_time
            energy_str = str(energy).ljust(next(lens))
            total_time_str = str(r.total_time).ljust(next(lens))
            parameters_str = ' '.join(map(str, [r.hotplug_in_load_limit,
                                                r.hotplug_out_load_limit,
                                                r.hotplug_in_sampling_period,
                                                r.hotplug_out_sampling_period,
                                                r.up_threshold,
                                                r.sched_olord_lb_upper_limit])).ljust(next(lens))
            print experiment_id_str, target_load_level_str, avg_power_str, energy_str, total_time_str, parameters_str

    def plot_pairs():
        from numpy import array
        from pandas import DataFrame
        from pandas.tools.plotting import scatter_matrix
        from csv import writer as csvwriter
        import matplotlib.pyplot as plt
        from subprocess import call

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])
        q = list(q)

        data = []

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.energy = r.avg_power * r.total_time
            r.the_class = 'bad'
            r.target_load_level = float(r.target_load_level)
            # ts = list(session.query(ExperimentData).filter_by(experiment_id = r.experiment_id))
            # for t in ts:
            #     data.append([t.power,
            #                  get_n_cpus(t),
            #                  float(r.target_load_level),
            #                  r.up_threshold])

        get_key_fn = lambda l: {'power': lambda r: ((l - r.target_load_level)**2, r.avg_power),
                                'energy': lambda r: ((l - r.target_load_level)**2, r.energy),
                                'time': lambda r: ((l - r.target_load_level)**2, r.total_time)}[config['selected_column']]

        for l in [0.2, 0.4, 0.6, 0.8]:
            q.sort(key=get_key_fn(l))
            for i in range(10):
                q[i].the_class = 'good'

        for i in range(len(q)):
            r = q[i]
            data.append([r.energy,
                         r.avg_power,
                         r.total_time,
                         r.hotplug_in_load_limit,
                         r.hotplug_out_load_limit,
                         r.hotplug_in_sampling_period,
                         r.up_threshold,
                         r.the_class
                         ])

        data.reverse() # Reverse plotting order in R

        out_data_file = "/tmp/asd.csv"
        out_code_file = "/tmp/asd2.r"
        out_pdf_file  = "/tmp/asd.pdf" if (config['selected_load'] == None) else ("/tmp/asd-%f.pdf" % config['selected_load'])

        r_code = \
"""
d <- read.csv("%s")
pdf("%s")
pairs(d[,1:6] ,pch=19,col=c("red","blue")[unclass(d$c)])
""" % (out_data_file, out_pdf_file)

        # data = map(lambda r: [r.energy,
        #                       r.avg_power,
        #                       r.total_time,
        #                       # float(r.target_load_level),
        #                       r.hotplug_in_load_limit,
        #                       r.hotplug_out_load_limit,
        #                       # r.hotplug_in_sampling_period,
        #                       # r.hotplug_out_sampling_period,
        #                       r.up_threshold,
        #                       # r.sched_olord_lb_upper_limit,
        #                       ], q)

        cols = ['energy',
                'avg. power',
                'total time',
                # 'target load level',
                'hotplug in load limit',
                'hotplug out load limit',
                'hotplug sampling period',
                # 'hotplug in sampling period',
                # 'hotplug out sampling period',
                'up threshold',
                'class'
                # 'sched olord lb upper limit',
                ]

        # cols = ['power',
        #         'cpus online',
        #         'target load level',
        #         'up threshold']

        cols = map(lambda s: ''.join(map(lambda q: q[0], s.split(" "))), cols)

        with open(out_data_file, "wb") as f:
            w = csvwriter(f)
            w.writerow(cols)
            for r in data:
                w.writerow(r)

        with open(out_code_file, "wb") as f:
            f.write(r_code)

        call(["R", '-f', out_code_file])


    def clustring():
        from scipy.cluster.vq import kmeans
        from numpy import array

        q = session.query(ExperimentInfo)

        if config['selected_load'] != None:
            q = q.filter_by(target_load_level = config['selected_load'])
        q = list(q)

        data = []

        for r in q:
            r.avg_power = get_avg_power(r.experiment_id)
            r.energy = r.avg_power * r.total_time
            data.append([r.energy,
                         r.hotplug_in_load_limit,
                         r.hotplug_out_load_limit,
                         r.hotplug_in_sampling_period,
                         r.hotplug_out_sampling_period,
                         r.up_threshold,
                         r.sched_olord_lb_upper_limit,
                         ])
        data = array(data)


        c, _ = kmeans(data, config['n_clusters'])

        print "Centriods:"
        print c

        # df = DataFrame(data[:10], columns = cols)
        # axes1 = scatter_matrix(df, alpha=0.2)
        # df = DataFrame(data[10:], columns = cols)
        # axes2 = scatter_matrix(df, alpha=0.2, marker='x')
        # plt.tight_layout()
        # plt.show()

    def calc_top_scores():
        q = session.query(ExperimentInfo)

        key_fn = {'power': lambda r: r.avg_power,
                  'energy': lambda r: r.energy,
                  'time': lambda r: r.total_time}[config['selected_column']]

        scores = {}

        for l in [0.2, 0.4, 0.6, 0.8]:
            print "Calculating scores for load level %f..." % l
            the_q = list(q.filter_by(target_load_level = l))

            for r in q:
                r.avg_power = get_avg_power(r.experiment_id)
                r.energy = r.avg_power * r.total_time

            the_q.sort(key=key_fn)

            for i in range(10):
                score = 10 - i
                e = the_q[i]
                k_str = '%i-%i-%i-%i' % (e.hotplug_in_load_limit,
                                         e.hotplug_out_load_limit,
                                         e.hotplug_in_sampling_period,
                                         e.up_threshold)
                if k_str in scores:
                    scores[k_str] += score
                else:
                    scores[k_str] = score

        scores = scores.items()
        scores.sort(key=lambda x: x[1])
        for s in scores:
            print s[0], s[1]

    if config["action"] == "list":
        list_experiments()
    elif config["action"] == "list_avgs":
        list_experiment_avgs()
    elif config["action"] == "show":
        show_experiement_props()
    elif config["action"] == "export":
        export_time_series()
    elif config["action"] == "histograms":
        plot_histograms()
    elif config["action"] == "list_sq_err":
        list_sort_sq_error()
    elif config["action"] == "parameters_in_range":
        list_parameters_in_range()
    elif config["action"] == "plot_pairs":
        plot_pairs()
    elif config["action"] == "clustring":
        clustring()
    elif config["action"] == "top_scores":
        calc_top_scores()

if __name__ == '__main__':
    main()
