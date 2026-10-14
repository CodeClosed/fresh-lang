#include <stdio.h>

int main(void) {
    int COUNT = 10000;
    long long total_sum = 0;
    int matched_count = 0;

    for (int i = 0; i < COUNT; i++) {
        long long val = (i * 7 + 13) % 1000;
        if (val > 50 && val % 2 == 0) {
            long long transformed = val * 3;
            total_sum += transformed;
            matched_count++;
        }
    }

    printf("Pipeline Completed. Matched: %d, Total Sum: %lld\n", matched_count, total_sum);
    return 0;
}
