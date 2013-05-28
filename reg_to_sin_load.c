/***********************************************************************************/
/* Copyright (c) 2013, Wictor Lund. All rights reserved.			   */
/* Copyright (c) 2013, Åbo Akademi University. All rights reserved.		   */
/* 										   */
/* Redistribution and use in source and binary forms, with or without		   */
/* modification, are permitted provided that the following conditions are met:	   */
/*      * Redistributions of source code must retain the above copyright	   */
/*        notice, this list of conditions and the following disclaimer.		   */
/*      * Redistributions in binary form must reproduce the above copyright	   */
/*        notice, this list of conditions and the following disclaimer in the	   */
/*        documentation and/or other materials provided with the distribution.	   */
/*      * Neither the name of the Åbo Akademi University nor the		   */
/*        names of its contributors may be used to endorse or promote products	   */
/*        derived from this software without specific prior written permission.	   */
/* 										   */
/* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND */
/* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED   */
/* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE	   */
/* DISCLAIMED. IN NO EVENT SHALL ÅBO AKADEMI UNIVERSITY BE LIABLE FOR ANY	   */
/* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES	   */
/* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;	   */
/* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND	   */
/* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT	   */
/* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS   */
/* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 		   */
/***********************************************************************************/

#include <sys/time.h>
#include <sys/resource.h>

#include <time.h>

#include <stdio.h>
#include <math.h>
#include <stdlib.h>

#include "operation.h"

#define CLOCK_TO_DOUBLE_S(c) ((double)(c) / (double)CLOCKS_PER_SEC)
#define TIMEVAL_TO_DOUBLE(t) ((t).tv_sec + (t).tv_usec / 1000000.0)

#define MIN_SLEEP_LENGTH (0.001)
#define MAX_SLEEP_LENGTH (0.002)

#define LOOP_M 100

#define RATIO (0.8)

#define ALPHA_T_O (0.5)

#define OUTER_LOOPS_PER_CYCLE 100
#define INITIAL_INNER_LOOPS_PER_CYCLE 1

#define LOOP_LENGTH_S (0.1)

double get_double_time()
{
	struct timeval t;
	gettimeofday(&t, NULL);

	return TIMEVAL_TO_DOUBLE(t);
}

double get_double_rusage_time()
{
	struct rusage r;
	getrusage(RUSAGE_SELF, &r);
	return TIMEVAL_TO_DOUBLE(r.ru_utime);
}

double get_double_clock_res()
{
	struct timespec ts;

	clock_getres(CLOCK_REALTIME, &ts);

	return ts.tv_sec + ts.tv_nsec/1000000000.0;
}

int main(int argc, char **argv)
{
	int i, j;
	double	load_ratio = 1.0;
	double  load_freq  = 0.05;
	double  load_shift = 0.0;
	double  load_max   = 0.0;
	double  load_min   = 0.0;
	int	loop_m	   = LOOP_M;
	int	loop_n	   = 100;

	double ft1;
	double ft2;
	double frt1;
	double frt2;
	double ft_diff;
	double frt_diff;
	double fstart_t = get_double_time();

	double clock_res = MIN_SLEEP_LENGTH;

	double t_o = 0.0;
	
	double fdelay = 0.0;
	double ftotal_delay = 0.0;

	double error_I = 0.0;

	int op_i;

	int total_nops = 0;
	double ftotal_time = 0.0;

	struct timespec delay = {
		.tv_sec = 0,
		.tv_nsec = 0
	};

	if (argc >= 4 && argc <= 5) {
		char	*eptr	  = NULL;
		load_max	  = strtod(argv[1], &eptr);
		load_min	  = strtod(argv[2], &eptr);
		load_shift	  = strtod(argv[3], &eptr);
		if (argc == 5)
			fstart_t  = strtod(argv[4], &eptr);
		else
			fstart_t  = get_double_time();
		load_max	 -= load_min;
	} else {
		printf("Invalid arguments.\n");
		return -1;
	}

	//clock_res = get_double_clock_res();
	//printf("clock_res = %f\n", clock_res);

	while (1) {
		ft1 = get_double_time();
		frt1 = get_double_rusage_time();

		for (op_i = 0; op_i < loop_m; op_i++) {
			for (j = 0; j < loop_n; j++) {
				operation();
			}
			nanosleep(&delay, NULL);
		}
		frt2 = get_double_rusage_time();
		ft2 = get_double_time();

		double the_cos = cos(load_freq * (ft2 - fstart_t) + load_shift);

		load_ratio = load_max*the_cos*the_cos + load_min;
		//printf("load_ratio = %f\n", load_ratio);

		total_nops += loop_m * loop_n;

		ft_diff	 = ft2 - ft1;
		frt_diff = frt2 - frt1;

		ftotal_time += ft_diff;

		double ops = (double)(loop_m * loop_n) / ft_diff;

		printf("%f, %f, %f, %f, %i\n", ft_diff, fdelay, ops, (double)total_nops / ftotal_time, total_nops);
		fflush(stdout);

		double t_m = frt_diff;
		//t_o = t_m / (double)(loop_m * loop_n);
		t_o = ALPHA_T_O*(t_m / (double)(loop_m * loop_n)) + (1.0 - ALPHA_T_O)*t_o;
		
		double k = (1-load_ratio)/load_ratio;

		double t_i = k * t_o;

		if (t_o == 0.0) {
			printf("ERROR: t_o estimated to 0.0\n");
			return -1;
		}

		loop_n = ceil(clock_res/t_i);
		if (loop_n == 0) {
			printf("ERROR: loop_n == 0\n");
			return -1;
		}

		fdelay = (double)loop_n * t_i;

		if (fdelay == 0.0) {
			printf("ERROR: fdelay == 0\n");
			return -1;
		}

		//printf("fdelay = %f, loop_n = %i, t_o = %f\n", fdelay, loop_n, t_o);

		delay.tv_sec = fdelay;
		delay.tv_nsec = fdelay*1000000000.0;
	}

}
