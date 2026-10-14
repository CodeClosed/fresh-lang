#include <stdio.h>
#include <stdlib.h>

#define N 64

int main(void) {
    double A[N][N];
    double B[N][N];
    double C[N][N];

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = 1.0;
            B[i][j] = 2.0;
            C[i][j] = 0.0;
        }
    }

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            double sum = 0.0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }

    printf("Matrix Multiply Completed. C[0][0] = %g, C[63][63] = %g\n", C[0][0], C[N-1][N-1]);
    return 0;
}
