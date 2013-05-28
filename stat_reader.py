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

class StatReader:
    def enqueue_output(self):
        from time import time, sleep
        time0 = time()
        while True:
            with open(self.filename) as f:
                d = map(lambda l: 
                        filter(lambda p: 
                               p != '', l.split(' ')), 
                        f.read().split('\n'))
                for l in d:
                    if len(l) == 0:
                        continue
                    if l[0] == 'cpu':
                        new_user       = int(l[1])
                        self.user_diff = new_user - self.user_last
                        self.user_last = new_user

                        new_nice       = int(l[2])
                        self.nice_diff = new_nice - self.nice_last
                        self.nice_last = new_nice

                        new_sys       = int(l[3])
                        self.sys_diff = new_sys - self.sys_last
                        self.sys_last = new_sys

                        new_idle       = int(l[4])
                        self.idle_diff = new_idle - self.idle_last
                        self.idle_last = new_idle

                        time1          = time()
                        self.idle_time = float(self.idle_diff) / float(time1 - time0)
                        time0          = time1
                        
                        total_diff = self.user_diff + self.nice_diff + self.sys_diff + self.idle_diff
                        self.idle_quot = 1.0 - float(total_diff - self.idle_diff) / float(total_diff)
            sleep(1.0)

    def __init__(self):
        from Queue import Queue
        from threading import Thread
        from functools import partial
        from os import sysconf_names, sysconf

        self.user_last = 0
        self.user_diff = 0
        self.user_time = 0

        self.nice_last = 0
        self.nice_diff = 0
        self.nice_time = 0

        self.sys_last = 0
        self.sys_diff = 0
        self.sys_time = 0

        self.idle_last = 0
        self.idle_diff = 0
        self.idle_time = 0

        self.filename = "/proc/stat"
        self.jiffy_hz = sysconf(sysconf_names['SC_CLK_TCK'])
        self.queue = Queue()
        self.thread = Thread(target=partial(StatReader.enqueue_output, self))
        self.thread.daemon = True
        self.thread.start()

class PsLoadLogger:
    def enqueue_output(self):
        from time import time
        while True:
            self.idle_quot = self.process.get_cpu_percent(interval=1.0)

    def __init__(self, pid):
        from psutil import Process
        from threading import Thread
        from functools import partial
        self.process = Process(pid)
        self.thread = Thread(target=partial(PsLoadLogger.enqueue_output, self))
        self.thread.daemon = True
        self.thread.start()

