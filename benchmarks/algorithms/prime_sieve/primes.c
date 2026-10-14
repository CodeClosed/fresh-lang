#include <stdio.h>
#include <stdbool.h>

long long count_primes(long long limit) {
    long long count = 0;
    for (long long n = 2; n <= limit; n++) {
        bool is_prime = true;
        for (long long d = 2; d * d <= n; d++) {
            if (n % d == 0) {
                is_prime = false;
                break;
            }
        }
        if (is_prime) {
            count++;
        }
    }
    return count;
}

int main(void) {
    long long total = count_primes(10000);
    printf("Primes count up to 10000: %lld\n", total);
    return 0;
}
