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
#include <time.h>

#include <stdio.h>
#include <math.h>
#include <stdlib.h>

#include "operation.h"

#define CLOCK_TO_DOUBLE_S(c) ((double)(c) / (double)CLOCKS_PER_SEC)
#define TIMEVAL_TO_DOUBLE(t) ((t).tv_sec + (t).tv_usec / 1000000.0)

#define MIN_SLEEP_LENGTH (0.001)
#define MAX_SLEEP_LENGTH (0.002)

#define RATIO (0.8)

#define OUTER_LOOPS_PER_CYCLE 100
#define INITIAL_INNER_LOOPS_PER_CYCLE 1

#define LOOP_LENGTH_S (0.1)

double get_double_time()
{
	struct timeval t;
	gettimeofday(&t, NULL);

	return TIMEVAL_TO_DOUBLE(t);
}

int main(int argc, char **argv)
{
	int i, j;
	int olpc = OUTER_LOOPS_PER_CYCLE;
	int ilpc = INITIAL_INNER_LOOPS_PER_CYCLE;
	double load_ratio = RATIO;

	double fstart_t;
	double ft1;
	double ft2;
	double ft_diff;
	
	double fdelay = 0.0;
	double ftotal_delay = 0.0;

	int op_i;

	int total_nops = 0;
	double ftotal_time = 0.0;

	struct timespec delay = {
		.tv_sec = 0,
		.tv_nsec = 0
	};
	
	fstart_t = get_double_time();

	if (argc == 2) {
		char *eptr = NULL;
		load_ratio = strtod(argv[1], &eptr);
		if (load_ratio == 0.0 && argv[1] == eptr) {
			printf("Invalid argument\n");
			return -1;
		}
	}

	while (1) {
		ft1 = get_double_time();
		for (op_i = 0; op_i < olpc; op_i++) {
			for (j = 0; j < ilpc; j++) {
				operation();
			}
			nanosleep(&delay, NULL);
		}
		ft2 = get_double_time();

		int lpc = ilpc * olpc;

		total_nops += lpc;

		ft_diff = ft2 - ft1;

		ftotal_time += ft_diff;

		double ops = (double)lpc / ft_diff;

		printf("%f, %f, %f, %f, %i\n", ft_diff, fdelay, ops, (double)total_nops / ftotal_time, total_nops);
		fflush(stdout);

		//ftotal_delay = ((1.0 - load_ratio)/load_ratio)*ft_diff;
		
		double k = (1.0 - load_ratio)/(load_ratio * (double)olpc);

		fdelay = k*(ft_diff - (double)olpc*fdelay);

		ftotal_delay = fdelay * (double)olpc;

		if (fdelay < MIN_SLEEP_LENGTH) {
			//ilpc = floor(ftotal_delay / (MIN_SLEEP_LENGTH * (double)olpc));
			ilpc += MIN_SLEEP_LENGTH / fdelay;
			//printf("fdelay too short, adjusted ilpc to %i.\n", ilpc);
		} else if (fdelay > MAX_SLEEP_LENGTH) {
			//ilpc = ceil(ftotal_delay / (MAX_SLEEP_LENGTH * (double)ilpc));
			ilpc -= MAX_SLEEP_LENGTH / fdelay;
			//printf("fdelay too long, adjusted ilpc to %i.\n", ilpc);
		}
		ilpc = ilpc <= 0 ? 1 : ilpc;
		
		lpc = ilpc * olpc;

		fdelay = ftotal_delay / (double)olpc;

		delay.tv_sec = fdelay;
		delay.tv_nsec = fdelay*1000000000.0;
	}

}
