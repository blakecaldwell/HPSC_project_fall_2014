#include <Profile/Profiler.h>

#line 1 "timing.c"
#include <stdlib.h>
#include <sys/time.h>

void get_walltime_(double* wcTime) {

#line 4

TAU_PROFILE_TIMER(tautimer, "void get_walltime_(double *) C [{timing.c} {4,1}-{8,1}]", " ", TAU_USER);
	TAU_PROFILE_START(tautimer);


#line 4
{
  struct timeval tp;
  gettimeofday(&tp, NULL);
  *wcTime = (double)(tp.tv_sec + tp.tv_usec/1000000.0);

#line 8

}
	
	TAU_PROFILE_STOP(tautimer);


#line 8
}

void get_walltime(double* wcTime) {

#line 10

TAU_PROFILE_TIMER(tautimer, "void get_walltime(double *) C [{timing.c} {10,1}-{12,1}]", " ", TAU_USER);
	TAU_PROFILE_START(tautimer);


#line 10
{
  get_walltime_(wcTime);

#line 12

}
	
	TAU_PROFILE_STOP(tautimer);


#line 12
}
