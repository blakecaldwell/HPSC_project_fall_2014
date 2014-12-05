CC = /projects/caldweba/tau-2.24/x86_64/bin/tau_cc.sh
FC = /projects/caldweba/tau-2.24/x86_64/bin/tau_f90.sh
LD = /projects/caldweba/tau-2.24/x86_64/bin/tau_f90.sh

export TAU_MAKEFILE=/projects/caldweba/tau-2.24/x86_64/lib/Makefile.tau-icpc-mpi-pdt
export TAU_TRACE=1

OPT = -Ofast -vec_report6 -simd -xhost -optKeepFiles
F90FLAGS = #-align all -fpe0 $(FFLAGS_DEBUG)
FFLAGS_DEBUG = #-g -traceback -O0 -check all -fp-model strict

mpi-jacobi.exe: timing.o mpi-jacobi.o
	$(LD) $(F90FLAGS) -o mpi-jacobi.exe timing.o mpi-jacobi.o

mpi-jacobi.o: mpi-jacobi.f90
	$(FC) $(F90FLAGS) $(OPT) -c mpi-jacobi.f90

timing.o: timing.c
	$(CC) $(OPT) -c timing.c

clean:
	rm -f *.o mpi-jacobi.exe
