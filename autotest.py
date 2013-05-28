#!/usr/bin/python
# -*- coding: utf-8 -*-
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

class TemperatureLogger:
    def run_thread(self):
        from time import sleep
        temp_file = '/sys/devices/platform/hkdk_tmu/curr_temp'
        while True:
            with open(temp_file) as f:
                d = f.read()
                self.temperature = float(d)
            sleep(1.0)
    def __init__(self):
        from threading import Thread
        from functools import partial
        self.thread = Thread(target=partial(TemperatureLogger.run_thread, self))
        self.thread.daemon = True
        self.thread.start()

class PowerSerialLogger:
    def run_thread(self):
        from StringIO import StringIO
        from csv import reader as csvreader

        with open(self.file) as open_file:
            iterator = iter(open_file.readline,b'')
            
            # Ignore rubbish in the beginning
            i = 0
            for line in iterator:
                i += 1
                if i > 50:
                    break

            for line in iterator:
                values = line.split(',')
                values = map(float, values)
                self.power = values[0] * values[1] * 10.0
                self.voltage = values[0]
                self.current = values[1] * 10.0
    def __init__(self):
        from threading import Thread
        from functools import partial
        self.file    = "/dev/ttyUSB0"
        self.power   = 0.0
        self.voltage = 0.0
        self.current = 0.0
        self.thread  = Thread(target=partial(PowerSerialLogger.run_thread, self))
        self.thread.daemon = True
        self.thread.start()

    def get_nowait(self):
        return self.power

proc_sys_kernel_olord_files = [
    'sched_olord_bi_directional',
    'sched_olord_cpu_load_limit',
    'sched_olord_cpu_period_lower_limit',
    'sched_olord_cpu_period_upper_limit',
    'sched_olord_ignore_IO',
    'sched_olord_ignore_nice',
    'sched_olord_lb_lower_limit',
    'sched_olord_lb_multiplier',
    'sched_olord_lb_upper_limit',
    'sched_olord_period',
    'sched_olord_rq_safety_margin'
    ]

sys_ondemand_files = [
    'hotplug_in_load_limit',
    'hotplug_in_sampling_period',
    'hotplug_out_load_limit',
    'hotplug_out_sampling_period',
    'up_threshold'
    ]

def read_maybe(file_name, maybe_str=""):
    try:
        with open(file_name) as f:
            return f.read()
    except:
        return maybe_str

def get_kernel_olord_settings():
    sys_kernel_olord_path = "/proc/sys/kernel/"
    ret = {}
    for name in proc_sys_kernel_olord_files:
        ret[name] = read_maybe(sys_kernel_olord_path + name, maybe_str="???")
    return ret

def get_ondemand_settings():
    sys_ondemand_path = "/sys/devices/system/cpu/cpufreq/ondemand/"
    ret = {}
    for name in sys_ondemand_files:
        ret[name] = read_maybe(sys_ondemand_path + name, maybe_str="???")
    return ret

def get_smt_mc_power_savings():
    smt_file = '/sys/devices/system/cpu/sched_smt_power_savings'
    mc_file = '/sys/devices/system/cpu/sched_mc_power_savings'
    return 'smt: ' + read_maybe(smt_file, maybe_str="???").strip() + ", mc: " + \
        read_maybe(mc_file, maybe_str="???")

def get_smt_mc_power_savings_old():
    smt_file = '/sys/devices/system/cpu/sched_smt_power_savings'
    mc_file = '/sys/devices/system/cpu/sched_mc_power_savings'
    try:
        with open(smt_file) as f:
            d = f.read().strip()
            ret += str(d)
    except:
        ret += '???'
    ret += ', mc: '
    try:
        with open(mc_file) as f:
            d = f.read().strip()
            ret += str(d)
    except:
        ret += '???'
    return ret

def get_governor_string():
    from glob import glob
    ret = ''
    for file_name in glob('/sys/devices/system/cpu/cpu?/cpufreq/scaling_governor'):
        with open(file_name) as f:
            d = f.read().strip()
            ret += d + " "
    return ret

def parse_arguments():
    return {}

def main():
    config = parse_arguments()
    from sqlalchemy import create_engine
    from sqlalchemy import Column, Table, MetaData
    from sqlalchemy import String, Integer, Float
    from sqlalchemy.orm import sessionmaker, mapper
    from sqlalchemy.ext.declarative import declarative_base
    from time import sleep
    from stat_reader import StatReader
    engine = create_engine('sqlite:///auto_test_log.sqlite')
    metadata = MetaData(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base = declarative_base()

    experiment_info = Table('experiment_info', metadata,
                            Column('experiment_id', String(32), primary_key=True),
                            Column('start_time', String()),
                            Column('end_time', String()),
                            Column('total_time', Float()),
                            Column('scheduler', String()),
                            Column('uname_a', String()),
                            Column('cpufreq_governor', String()),
                            Column('mt_mc_state', String()),
                            Column('target_load_level', String()),
                            Column('num_of_process', String()))
    
    
    for c_name in proc_sys_kernel_olord_files:
        experiment_info.append_column(Column(c_name, Float))

    for c_name in sys_ondemand_files:
        experiment_info.append_column(Column(c_name, Float))

    experiment_data = Table('experiment_data', metadata,
                            Column('data_id', String(48), primary_key=True),
                            Column('experiment_id', String(32)),
                            Column('time', Float()),
                            Column('voltage', Float),
                            Column('current', Float),
                            Column('power', Float),
                            Column('temperature', Float))

    metadata.create_all()

    class ExperimentInfo(Base):
        __table__ = experiment_info

    class ExperimentData(Base):
        __table__ = experiment_data

    eii = experiment_info.insert()
    eid = experiment_data.insert()

    psl = PowerSerialLogger()
    tl  = TemperatureLogger()

    def perform_experiment_a(experiment_config):
        from md5 import new as new_md5
        from pickle import dumps as pickle_dump
        from platform import uname
        from datetime import datetime
        from time import time
        from threading import Thread
        from pprint import PrettyPrinter
        from simple_run import run_test

        pp = PrettyPrinter(indent = 4)
        print "Running experiment with config:"
        pp.pprint(experiment_config)

        current_experiment_id = new_md5(pickle_dump(experiment_config) + str(datetime.now())).hexdigest()
        info_dict = {'experiment_id': current_experiment_id,
                     'start_time': str(datetime.now()),
                     'scheduler': experiment_config['scheduler'],
                     'uname_a': ' '.join(uname()),
                     'cpufreq_governor': get_governor_string(),
                     'mt_mc_state': get_smt_mc_power_savings(),
                     'target_load_level': experiment_config['target_load_level'],
                     'num_of_process': experiment_config['num_of_process'],
                     'num_of_ops': experiment_config['num_of_ops']}
        info_dict.update(get_kernel_olord_settings())
        info_dict.update(get_ondemand_settings())

        eii.execute(info_dict)
        test_args = {'n': experiment_config['num_of_process'],
                     'a': 'dont_set',
                     'l': experiment_config['target_load_level'],
                     'o': experiment_config['num_of_ops']}
        
        class TestThread(Thread):
            def __init__(self, args):
                self.args = args
                Thread.__init__(self)
            def run(self):
                self.total_time = run_test(self.args)

        tt = TestThread(test_args)
        tt.start()

        start_time = time()
        
        data_counter = 0
        while tt.is_alive():
            t = time() - start_time
            data_dict = {'data_id': current_experiment_id + str(data_counter).zfill(16),
                         'experiment_id': current_experiment_id,
                         'time': t,
                         'voltage': psl.voltage,
                         'current': psl.current,
                         'power': psl.power,
                         'temperature': tl.temperature}
            eid.execute(data_dict)
            sleep_time = 1.0 - time() + (t + start_time)
            sleep_time = 0.0 if (sleep_time < 0) else sleep_time
            #print sleep_time
            sleep(sleep_time)
            data_counter += 1

        r = session.query(ExperimentInfo).filter_by(experiment_id = current_experiment_id).first()
        r.end_time = str(datetime.now())
        r.total_time = float(tt.total_time)
        session.commit()

    for i in range(10):
        sleep(10.0)
        perform_experiment_a({'scheduler': 'OGS',
                              'target_load_level': 0.8,
                              'num_of_process': 4,
                              'num_of_ops': 100000})
        sleep(10.0)
        perform_experiment_a({'scheduler': 'OGS',
                              'target_load_level': 0.6,
                              'num_of_process': 4,
                              'num_of_ops': 100000})
        sleep(10.0)
        perform_experiment_a({'scheduler': 'OGS',
                              'target_load_level': 0.4,
                              'num_of_process': 4,
                              'num_of_ops': 100000})
        sleep(10.0)
        perform_experiment_a({'scheduler': 'OGS',
                              'target_load_level': 0.2,
                              'num_of_process': 4,
                              'num_of_ops': 100000})

if __name__ == '__main__':
    main()
