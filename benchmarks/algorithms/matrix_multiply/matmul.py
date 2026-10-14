N = 64

A = [[1.0 for _ in range(N)] for _ in range(N)]
B = [[2.0 for _ in range(N)] for _ in range(N)]
C = [[0.0 for _ in range(N)] for _ in range(N)]

for i in range(N):
    for j in range(N):
        total = 0.0
        for k in range(N):
            total += A[i][k] * B[k][j]
        C[i][j] = total

print(f"Matrix Multiply Completed. C[0][0] = {C[0][0]}, C[63][63] = {C[N-1][N-1]}")
