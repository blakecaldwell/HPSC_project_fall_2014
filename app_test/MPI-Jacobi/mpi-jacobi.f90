!! Adapted from class iPython notebook by Thomas Hauser
!! and MPI Jacobi section of G. Hager's textbook.
!! Dan Milroy

PROGRAM mpi_jacobi

  USE MPI

  IMPLICIT NONE
  DOUBLE PRECISION, ALLOCATABLE :: phi(:,:,:,:)
  DOUBLE PRECISION :: MFLOPS
  DOUBLE PRECISION :: WT, WTT, S, E ! Timing variables 
  DOUBLE PRECISION :: east, west, north, south, top, bottom ! Init conditions
  DOUBLE PRECISION :: maxdelta ! max difference between grid points
  INTEGER, DIMENSION(1:3) :: problem_size, proc_dims, cart_dims, my_cart_coords
  INTEGER :: i, j, k, iter ! Some iterators
  INTEGER :: imax, jmax, kmax, niter, bi, bj, bk ! Problem size and block sizes
  INTEGER :: t0, t1, tmp, displ, direction
  INTEGER :: my_rank, ierror, numProcs, req(6), stats(MPI_STATUS_SIZE) ! Initial communicator setup.
  INTEGER :: CART_COMM_WORLD, my_rank_cart, numProcs_cart, source, dest ! Cartesian comm values
  INTEGER :: iStart, iEnd, jStart, jEnd, kStart, kEnd, tag ! local prob size
  INTEGER(KIND=8), DIMENSION(1:3) :: msgsize
  DOUBLE PRECISION, ALLOCATABLE :: fieldSend(:), fieldRecv(:)
  INTEGER(KIND=8) :: bufLen

  LOGICAL, DIMENSION(1:3) :: pbc_check ! For periodic boundary conditions, set to
  ! false below
  LOGICAL :: reorder ! set to true below.
  CHARACTER(len=100) :: char_buffer

!  ierror = 0
! Start MPI
  CALL MPI_Init(ierror)
  CALL MPI_Comm_rank(MPI_COMM_WORLD, my_rank, ierror)
  CALL MPI_Comm_size(MPI_COMM_WORLD, numProcs, ierror)

! Rank 0 reads the command line arguments and broadcasts them to the other
! ranks.
  IF (my_rank.EQ.0) THEN

! Must use this dumb construct because Fortran is bad at parsing arguments.
! This was simpler, but doesn't work if the argument order changes.
    CALL GET_COMMAND_ARGUMENT(2, char_buffer)
    READ(char_buffer, '(I10)') imax
    CALL GET_COMMAND_ARGUMENT(4, char_buffer)
    READ(char_buffer, '(I10)') jmax
    CALL GET_COMMAND_ARGUMENT(6, char_buffer)
    READ(char_buffer, '(I10)') kmax
    CALL GET_COMMAND_ARGUMENT(8, char_buffer)
    READ(char_buffer, '(D10.0)') east
    CALL GET_COMMAND_ARGUMENT(10, char_buffer)
    READ(char_buffer, '(D10.0)') west
    CALL GET_COMMAND_ARGUMENT(12, char_buffer)
    READ(char_buffer, '(D10.0)') north
    CALL GET_COMMAND_ARGUMENT(14, char_buffer)
    READ(char_buffer, '(D10.0)') south
    CALL GET_COMMAND_ARGUMENT(16, char_buffer)
    READ(char_buffer, '(D10.0)') top
    CALL GET_COMMAND_ARGUMENT(18, char_buffer)
    READ(char_buffer, '(D10.0)') bottom
    CALL GET_COMMAND_ARGUMENT(20, char_buffer)
    READ(char_buffer, '(I20)') niter
    
    proc_dims(:) = 0
    pbc_check(:) = .false.
    problem_size(1) = imax
    problem_size(2) = jmax
    problem_size(3) = kmax

  ENDIF

! Broadcast inputs to the other ranks.
  CALL MPI_Bcast(problem_size, 3, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(proc_dims, 3, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(pbc_check, 3, MPI_LOGICAL, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(imax, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(jmax, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(kmax, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(niter, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(east, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(west, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(north, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(south, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(top, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)
  CALL MPI_Bcast(bottom, 1, MPI_DOUBLE_PRECISION, 0, MPI_COMM_WORLD, ierror)


! Now set up the Cartesian communicator.
  CALL MPI_Dims_create(numProcs, 3, proc_dims, ierror)

  reorder = .true.
  CALL MPI_Cart_create(MPI_COMM_WORLD, 3, proc_dims, pbc_check, reorder, &
                        CART_COMM_WORLD, ierror)


! Get the new rank and comm size, and coordinates
  CALL MPI_Comm_rank(CART_COMM_WORLD, my_rank_cart, ierror)
  CALL MPI_Comm_size(CART_COMM_WORLD, numProcs_cart, ierror)
  CALL MPI_Cart_coords(CART_COMM_WORLD, my_rank_cart, 3, my_cart_coords, ierror)


! Set up local subdomains.
  DO i = 1, 3
    cart_dims(i) = problem_size(i)/proc_dims(i)
    IF (my_cart_coords(i).LT.MOD(problem_size(i), proc_dims(i))) THEN
      cart_dims(i) = cart_dims(i) + 1
    ENDIF
  ENDDO

  iStart = 0; iEnd = cart_dims(1) + 1
  jStart = 0; jEnd = cart_dims(2) + 1
  kStart = 0; kEnd = cart_dims(3) + 1


! Allocate and zero phi
  ALLOCATE(phi(iStart:iEnd, jStart:jEnd, kStart:kEnd, 0:1))
  phi(:,:,:,:) = 0.d0

! Set up the buffer
  bufLen = 0
  msgsize(3) = cart_dims(1)*cart_dims(2)
  bufLen = MAX(bufLen, msgsize(3)) 

  msgsize(2) = cart_dims(1)*cart_dims(3)
  bufLen = MAX(bufLen, msgsize(2))

  msgsize(1) = cart_dims(2)*cart_dims(3)
  bufLen = MAX(bufLen, msgsize(1))

  ALLOCATE(fieldRecv(1:bufLen))
  ALLOCATE(fieldSend(1:bufLen))
  fieldSend(:) = 0.d0; fieldRecv(:) = 0.d0

! Now the main loop.  Adapted from Hager's text.
  WTT = 0.d0; WT = 0.d0
  t0 = 0; t1 = 1
  tag = 0
  DO iter = 1, niter
    DO displ = -1, 1, 2
      DO direction = 1, 3

! Start the timer and calculate the shift
        CALL get_walltime(S)

        CALL MPI_Cart_shift(CART_COMM_WORLD, (direction-1), displ, source, & 
                            dest, ierror)

! Set the boundary conditions on the edges on the first iteration
        IF(source.EQ.MPI_PROC_NULL.AND.iter.EQ.1) THEN
          CALL setBoundaries(phi(:,:,:,:), &
                             iStart, jStart, kStart, iEnd, &
                             jEnd, kEnd, displ, direction, north, south, &
                             east, west, top, bottom)

        ELSEIF(source.NE.MPI_PROC_NULL) THEN
          CALL MPI_Irecv(fieldRecv(1), msgsize(direction), & 
                         MPI_DOUBLE_PRECISION, source, tag, &
                         CART_COMM_WORLD, req(6), ierror)
        ENDIF

        IF(dest.EQ.MPI_PROC_NULL.AND.iter.EQ.1) THEN
          CALL setBoundaries(phi(:,:,:,:), &
                             iStart, jStart, kStart, iEnd, &
                             jEnd, kEnd, displ, direction, north, south, &
                             east, west, top, bottom)
        ELSEIF(dest.NE.MPI_PROC_NULL) THEN
          CALL CopySendBuf(phi(:,:,:,t0), &
                           iStart, jStart, kStart, iEnd, jEnd, &
                           kEnd, displ, direction, fieldSend, bufLen)
          
          CALL MPI_Send(fieldSend(1), msgsize(direction), MPI_DOUBLE_PRECISION, &
                        dest, tag, CART_COMM_WORLD, ierror)

        ENDIF

        IF(source.NE.MPI_PROC_NULL) THEN
          call MPI_Wait(req(6), stats, ierror)

          call CopyRecvBuf(phi(:,:,:,t0), &
                           iStart, jStart, kStart, iEnd, jEnd, &
                           kEnd, displ, direction, fieldRecv, bufLen)
        ENDIF ! source exists

      ENDDO ! direction
    ENDDO ! displ

! Do the local Jacobi sweep
    CALL jacobi_sweep(phi(:,:,:,:), cart_dims(1), &
                      cart_dims(2), cart_dims(3), t0, t1, maxdelta)

! Now an allreduce to find the global maxdelta
    CALL MPI_Allreduce(MPI_IN_PLACE, maxdelta, 1, MPI_DOUBLE_PRECISION, & 
                       MPI_MAX, CART_COMM_WORLD, ierror)

! Stop the timer
    CALL get_walltime(E)

    WT = E - S
    WTT = WTT + WT
    
    tmp=t0; t0=t1; t1=tmp
  ENDDO ! Main loop

  IF (my_rank.EQ.0) THEN
    WRITE(*,*) "Wall time/iter: ",(WTT/niter),"Max delta: ",maxdelta
  ENDIF

  ! Shut it down
  CALL MPI_Finalize(ierror)

! Deallocate the arrays
  DEALLOCATE(phi, fieldSend, fieldRecv)

CONTAINS

  SUBROUTINE CopySendBuf(phi, iStart, jStart, kStart, iEnd, jEnd, &
                         kEnd, displ, direction, fieldSend, bufLen)
    IMPLICIT NONE
    INTEGER, INTENT(in) :: iStart, iEnd, jStart, jEnd, kStart, kEnd, displ, direction
    INTEGER :: i, j, k
    INTEGER(KIND=8), INTENT(in) :: bufLen
    DOUBLE PRECISION, DIMENSION(1:bufLen), INTENT(inout) :: fieldSend
    DOUBLE PRECISION, DIMENSION(iStart:iEnd, jStart:jEnd, kStart:kEnd, 0:1), &
      INTENT(inout) :: phi
    
    IF(direction.EQ.1) THEN 
      IF(displ.EQ.1) THEN ! send in positive i (j,k plane)
        !DIR$ SIMD
        DO i = 1, (jEnd - 1)
          DO j = 1, (kEnd - 1)
            fieldSend((i-1)*(kEnd-1) + j) = phi((iEnd-1), i, j, 0)
          ENDDO
        ENDDO
   
      ELSE ! send in negative i (j,k plane)
        !DIR$ SIMD
        DO i = 1, (jEnd - 1)
          DO j = 1, (kEnd - 1)
            fieldSend((i-1)*(kEnd-1) + j) = phi((iStart+1), i, j, 0)
          ENDDO
        ENDDO
      ENDIF
    ENDIF

    IF(direction.EQ.2) THEN 
      IF(displ.EQ.1) THEN ! send in positive j (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (kEnd - 1)
            fieldSend((i-1)*(kEnd-1) + j) = phi(i, (jEnd-1), j, 0)
          ENDDO
        ENDDO
      ELSE ! send in negative j (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (kEnd - 1)
            fieldSend((i-1)*(kEnd-1) + j) = phi(i, (jStart+1), j, 0)
          ENDDO
        ENDDO
      ENDIF ! disp
    ENDIF ! direct

    IF(direction.EQ.3) THEN 
      IF(displ.EQ.1) THEN ! send in positive k (i,j plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (jEnd - 1)
            fieldSend((i-1)*(jEnd-1) + j) = phi(i, j, (kEnd-1), 0)
          ENDDO
        ENDDO
      ELSE ! send in negative k (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (jEnd - 1)
            fieldSend((i-1)*(jEnd-1) + j) = phi(i, j, (kStart+1), 0)
          ENDDO
        ENDDO
      ENDIF ! disp
    ENDIF ! direct

  END SUBROUTINE CopySendBuf

  SUBROUTINE CopyRecvBuf(phi,iStart, jStart, kStart, iEnd, jEnd, &
                           kEnd, displ, direction, fieldRecv, bufLen)
    IMPLICIT NONE
    INTEGER, INTENT(in) :: iStart, iEnd, jStart, jEnd, kStart, kEnd, displ, direction
    INTEGER :: i, j, k
    INTEGER(KIND=8), INTENT(in) :: bufLen
    DOUBLE PRECISION, DIMENSION(1:bufLen), INTENT(in) :: fieldRecv
    DOUBLE PRECISION, DIMENSION(iStart:iEnd, jStart:jEnd, kStart:kEnd, 0:1), &
      INTENT(inout) :: phi

    IF(direction.EQ.1) THEN 
      IF(displ.EQ.1) THEN ! receive from positive i (j,k plane)
        !DIR$ SIMD
        DO i = 1, (jEnd - 1)
          DO j = 1, (kEnd - 1)
            phi(iEnd, i, j, 0) = fieldRecv((i-1)*(kEnd-1) + j)
          ENDDO
        ENDDO
      ELSE ! receive from negative i (j,k plane)
        !DIR$ SIMD
        DO i = 1, (jEnd - 1)
          DO j = 1, (kEnd - 1)
            phi(iStart, i, j, 0) = fieldRecv((i-1)*(kEnd-1) + j)
          ENDDO
        ENDDO
      ENDIF ! disp
    ENDIF ! direct

    IF(direction.EQ.2) THEN 
      IF(displ.EQ.1) THEN ! receive from positive j (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (kEnd - 1)
            phi(i, jEnd, j, 0) = fieldRecv((i-1)*(kEnd-1) + j)
          ENDDO
        ENDDO
      ELSE ! receive from negative j (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (kEnd - 1)
            phi(i, jStart, j, 0) = fieldRecv((i-1)*(kEnd-1) + j)
          ENDDO
        ENDDO
      ENDIF ! disp
    ENDIF ! direct

    IF(direction.EQ.3) THEN 
      IF(displ.EQ.1) THEN ! receive from positive k (i,j plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (jEnd - 1)
            phi(i, j, kEnd, 0) = fieldRecv((i-1)*(jEnd-1) + j)
          ENDDO
        ENDDO
      ELSE ! receive from negative j (i,k plane)
        !DIR$ SIMD
        DO i = 1, (iEnd - 1)
          DO j = 1, (jEnd - 1)
            phi(i, j, kStart, 0) = fieldRecv((i-1)*(jEnd-1) + j)
          ENDDO
        ENDDO
      ENDIF ! disp
    ENDIF ! direct

  END SUBROUTINE CopyRecvBuf

  SUBROUTINE setBoundaries(phi, iStart, jStart, kStart, iEnd, jEnd, &
                           kEnd, displ, direction, north, south, east, &
                           west, top, bottom)
    IMPLICIT NONE
    DOUBLE PRECISION, INTENT(in) :: north, south, east, west, top, &
                                     bottom
    DOUBLE PRECISION, DIMENSION(iStart:iEnd, jStart:jEnd, kStart:kEnd, 0:1), &
      INTENT(inout) :: phi
    INTEGER, INTENT(in) :: iStart, iEnd, jStart, jEnd, kStart, kEnd, displ, direction
    INTEGER :: i, j, k

    IF(direction.EQ.1) THEN ! i (j,k plane)
      IF(displ.EQ.1) THEN ! positive
        phi(iEnd, jStart:jEnd, kStart:kEnd, :) = north
      ELSEIF(displ.EQ.(-1)) THEN ! negative
        phi(iStart, jStart:jEnd, kStart:kEnd, :) = south
      ENDIF
    ENDIF

    IF(direction.EQ.2) THEN ! j (i,k plane)
      IF(displ.EQ.1) THEN ! positive
        phi(iStart:iEnd, jEnd, kStart:kEnd, :) = top
      ELSEIF(displ.EQ.(-1)) THEN ! negative
        phi(iStart:iEnd, jStart, kStart:kEnd, :) = bottom
      ENDIF
    ENDIF

    IF(direction.EQ.3) THEN ! k (i,j plane)
      IF(displ.EQ.1) THEN ! positive
        phi(iStart:iEnd, jStart:jEnd, kEnd, :) = west
      ELSEIF(displ.EQ.(-1)) THEN ! negative
        phi(iStart:iEnd, jStart:jEnd, kStart, :) = east
      ENDIF
    ENDIF

  END SUBROUTINE setBoundaries

  SUBROUTINE jacobi_sweep(phi, nx, ny, nz, t0, t1, maxdelta)
  IMPLICIT NONE
  DOUBLE PRECISION, DIMENSION(0:nx+1,0:ny+1,0:nz+1, 0:1), INTENT(inout) :: phi
  DOUBLE PRECISION, INTENT(out) :: maxdelta
  DOUBLE PRECISION :: D
  INTEGER, INTENT(inout) :: nx, ny, nz, t0, t1
  INTEGER :: i, j, k, tmp

  D = 1.d0/6.d0

  !DIR$ SIMD
  DO k = 1, nz
    DO j = 1, ny
      DO i = 1, nx
        phi(i,j,k,t1) = (phi(i+1, j, k, t0) + phi(i-1, j, k, t0) + &
                              phi(i, j+1, k, t0) + phi(i, j-1, k, t0) + &
                              phi(i, j, k+1, t0) + phi(i, j, k-1, t0)) * D
      ENDDO ! i
    ENDDO ! j
  ENDDO ! k      
  
  maxdelta = MAXVAL(ABS(phi(:,:,:,t1) - phi(:,:,:,t0)))
  END SUBROUTINE jacobi_sweep

END PROGRAM mpi_jacobi
