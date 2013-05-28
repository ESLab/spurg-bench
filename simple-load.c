
#include <sys/time.h>
#include <time.h>

#include <stdio.h>
#include <math.h>

#define SLEEPS_PER_MEASURE 10

#define OPS_PER_MEASURE 10

#define CALIBRATION_MEASUREMENTS 1

#define RATIO 0.6

#define TIMEVAL_TO_DOUBLE(t) ((t).tv_sec + (t).tv_usec / 1000000.0)
#define TIMEVAL_TO_TVI(t)    ((t).tv_sec * 1000000 + (t).tv_usec)

int operation()
{
	int i;
	double a = 2.0;
	for (i = 0; i < 10000000; i++) {
		a *= 2.0;
	}
}

typedef long long int tv_int_t;

int main()
{
	struct timeval t1;
	struct timeval t2;
	clock_t ct1;
	clock_t ct2;

	double ft1;
	double ft2;
	double cft1;
	double cft2;

	double ft_diff;
	double cft_diff;
	double tpo;
	
	double k = (1.0-RATIO)/(RATIO*OPS_PER_MEASURE);
	
	double cal[CALIBRATION_MEASUREMENTS];
	int cal_i;

	int op_i;

	struct timespec delay = { 
		.tv_sec = 0, 
		.tv_nsec = 0
	};
	double fdelay = 0.0;

	while (1) {
		gettimeofday(&t1, NULL);
		ct1 = clock();
		
		for (op_i = 0; op_i < OPS_PER_MEASURE; op_i++) {
			operation();
			nanosleep(&delay, NULL);
		}
		
		gettimeofday(&t2, NULL);
		ct2 = clock();


		#if 0
		it1 = TIMEVAL_TO_TVI(t1);
		it2 = TIMEVAL_TO_TVI(t2);
		
		it_diff = it2 - it1;
		#endif
		
		ft1 = TIMEVAL_TO_DOUBLE(t1);
		ft2 = TIMEVAL_TO_DOUBLE(t2);

		cft1 = (double)ct1 / (double)CLOCKS_PER_SEC;
		cft2 = (double)ct2 / (double)CLOCKS_PER_SEC;
		
		ft_diff = ft2 - ft1;
		cft_diff = cft2 - cft1;
		
		fdelay = ((1.0-RATIO)/RATIO)*cft_diff/(double)OPS_PER_MEASURE;

		delay.tv_sec = fdelay;
		delay.tv_nsec = fdelay*1000000000.0;

		double total_delay = OPS_PER_MEASURE*fdelay;

		double fop_t = 1.0 - total_delay / ft_diff;

		//printf("total_time = %f, delay = %f, total_delay = %f, load = %f\n", ft_diff, fdelay, total_delay, 1.0 -  total_delay / ft_diff);
		printf("%f, %f, %f, %f, %f\n", ft_diff, fdelay, ft_diff - total_delay, fop_t, cft_diff);
		fflush(stdout);
	}


}
