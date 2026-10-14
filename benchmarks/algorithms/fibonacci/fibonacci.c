#include <stdio.h>

long long fib(long long n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main(void) {
    long long result = fib(20);
    printf("Result: %lld\n", result);
    return 0;
}
