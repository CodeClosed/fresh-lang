#include <stdio.h>
#include <stdlib.h>

#define SIZE 2000

void quicksort(long long arr[], int low, int high) {
    if (low < high) {
        long long pivot = arr[high];
        int i = low - 1;
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                long long tmp = arr[i];
                arr[i] = arr[j];
                arr[j] = tmp;
            }
        }
        int p_idx = i + 1;
        long long tmp2 = arr[p_idx];
        arr[p_idx] = arr[high];
        arr[high] = tmp2;

        quicksort(arr, low, p_idx - 1);
        quicksort(arr, p_idx + 1, high);
    }
}

int main(void) {
    long long arr[SIZE];
    long long seed = 42;
    for (int i = 0; i < SIZE; i++) {
        seed = (seed * 1103515245 + 12345) % 2147483647;
        arr[i] = seed % 10000;
    }

    quicksort(arr, 0, SIZE - 1);
    printf("QuickSort Completed. Min: %lld, Max: %lld\n", arr[0], arr[SIZE - 1]);
    return 0;
}
