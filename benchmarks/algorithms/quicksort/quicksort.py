SIZE = 2000

def quicksort(arr, low, high):
    if low < high:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        p_idx = i + 1
        arr[p_idx], arr[high] = arr[high], arr[p_idx]

        quicksort(arr, low, p_idx - 1)
        quicksort(arr, p_idx + 1, high)

arr = []
seed = 42
for _ in range(SIZE):
    seed = (seed * 1103515245 + 12345) % 2147483647
    arr.append(seed % 10000)

quicksort(arr, 0, SIZE - 1)
print(f"QuickSort Completed. Min: {arr[0]}, Max: {arr[SIZE - 1]}")
