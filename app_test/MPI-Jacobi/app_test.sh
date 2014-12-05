#!/bin/bash

#SBATCH -J route_test

#SBATCH --time=01:00:00

#SBATCH --account=crcbenchmark

#SBATCH --reservation=ib-testing

#SBATCH --nodes=40

#SBATCH --ntasks-per-node 12

#SBATCH --qos janus

#SBATCH --output=/home/dami9546/CSCI5576/project/app_test/app.out

module load tau/tau-2.22.2_openmpi-1.6.4_intel-13.0.0_ib
module load HPSC_CLASS2014/hw06

export TAU_TRACE=1

srun -N40 /home/dami9546/CSCI5576/project/app_test/wrapper.sh begin

cd /home/dami9546/CSCI5576/project/app_test/MPI-Jacobi

tau_exec mpirun -np 12 ./mpi-jacobi.exe -imax 2730 -jmax 2730 -kmax 2730 -east 0 -west 0 -north 1 -south 0 -top 0 -bottom 0 -niter 1000

srun -N40 /home/dami9546/CSCI5576/project/app_test/wrapper.sh end 
