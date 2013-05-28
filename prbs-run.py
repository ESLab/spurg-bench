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

class LoadProcess:
    def enqueue_output(self):
        for line in iter(self.process.stdout.readline, b''):
            self.queue.put(line)
            self.process.stdin.write(str(self.load))
            self.process.stdin.flush()
        self.process.stdout.close()
    def __init__(self, binary, *args):
        from subprocess import Popen, PIPE
        from Queue import Queue
        from threading import Thread
        from functools import partial
        from os import setsid
        from datetime import datetime
        self.load = 0.5
        self.process = Popen([binary] + list(args), stdin=PIPE, stdout=PIPE, bufsize=1, close_fds=True, preexec_fn=setsid)
        self.start_time = datetime.now()
        self.queue = Queue()
        self.thread = Thread(target=partial(LoadProcess.enqueue_output, self))
        self.thread.daemon = True
        self.thread.start()

    def set_load(self, load_val):
        self.load = load_val
    
    def get_nowait(self):
        try: 
            l = self.queue.get_nowait()
        except:
            l = None
        return l
    
    def get(self, timeout=None):
        if timeout != None:
            self.queue.get(True, timeout)
        else:
            self.queue.get(True)

def the_loop(proc, args):
    from time import sleep, time
    data = list(map(lambda a: [0,0,0,0], range(args.n[0])))
    t = time()

    while True:
        i = 0
        got_something = False
        for p in proc:
            from Queue import Empty
            
            l = p.get_nowait()
            if l != None:
                from StringIO import StringIO
                from csv import reader as csvreader
                f = StringIO(l)
                r = csvreader(f, delimiter=',')
                for row in r:
                    data[i] = map(lambda s: float(s), row)
                    #print "From process %i:" % i, data[i]
                got_something = True
            i += 1
        if time() > t + 5:
            from random import randint
            t = time()
            r = randint(0,1)
            l = args.min[0]
            if r == 1:
                l = args.max[0]
            for p in proc:
                p.set_load(l)
            print "Set load to ", l
        if not got_something:
            sleep(1.0)
        else:
            #print map(lambda l: (0,0,0,0,0) if len(l) < 5 else (l[2], l[2] - l[3], l[4]), data)
            if args.o[0] > 0:
                if sum(map(lambda l: 0 if len(l) < 5 else l[4], data)) > args.o[0]:
                    print 'Reached %i operations, exiting...' % args.o[0]
                    return


def main():
    from argparse import ArgumentParser
    from time import time
    parser = ArgumentParser()
    parser.add_argument('-n', nargs=1, default=[1], type=int, help="Number of processes to start")
    parser.add_argument('-a', nargs=1, default=['dont_set'], choices=['dont_set', 'set'], help="Affinity setting")
    parser.add_argument('-max', nargs=1, default=[0.9], type=float, help="The maximum load to set on processes")
    parser.add_argument('-min', nargs=1, default=[0.1], type=float, help="The minium load to set on processes")
    parser.add_argument('-o', nargs=1, default=[0], type=int, help="Total number of operations to perform before exiting")
    args = parser.parse_args()

    n = args.n[0]

    proc_start_time = time()

    proc = map(lambda a: LoadProcess("./a.out"), range(n))
    for p in proc:
        p.set_load(args.min[0])

    if args.a == 'set':
        from multiprocessing import cpu_count
        from schedutils      import set_affinity
        cpus = cpu_count()
        i = 0
        for p in proc:
            set_affinity(p.pid, [i])
            i += 1
    
    try:
        the_loop(proc, args)
    finally:
        from os import killpg
        from signal import SIGTERM
        from datetime import datetime
        start_time = min(map(lambda p: p.start_time, proc))
        end_time   = datetime.now()
        print "Configuration:", args
        print "Total running time:", end_time - start_time
        print "Killing processes..."
        map(lambda p: killpg(p.process.pid, SIGTERM), proc)



if __name__ == '__main__':
    main()
