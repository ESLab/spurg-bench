
#include <sys/time.h>

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

	//tv_int_t it1;
	//tv_int_t it2;

	double ft1;
	double ft2;

	double ft_diff;
	//tv_int_t it_diff;
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

	printf("k = %f\n", k);
	

	while (1) {
		gettimeofday(&t1, NULL);
		
		for (op_i = 0; op_i < OPS_PER_MEASURE; op_i++) {
			operation();
			nanosleep(&delay);
		}
		
		gettimeofday(&t2, NULL);

		#if 0
		it1 = TIMEVAL_TO_TVI(t1);
		it2 = TIMEVAL_TO_TVI(t2);
		
		it_diff = it2 - it1;
		#endif
		
		ft1 = TIMEVAL_TO_DOUBLE(t1);
		ft2 = TIMEVAL_TO_DOUBLE(t2);
		
		ft_diff = ft2 - ft1;
		
		fdelay = k*(ft_diff - OPS_PER_MEASURE*fdelay);

		delay.tv_sec = fdelay;
		delay.tv_nsec = fdelay*1000000000.0;

		double total_delay = OPS_PER_MEASURE*fdelay;

		printf("total_time = %f, delay = %f, total_delay = %f, load = %f\n", ft_diff, fdelay, total_delay, 1.0 -  total_delay / ft_diff);
	}


}
