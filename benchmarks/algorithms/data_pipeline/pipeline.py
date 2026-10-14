COUNT = 10000
total_sum = 0
matched_count = 0

for i in range(COUNT):
    val = (i * 7 + 13) % 1000
    if val > 50 and val % 2 == 0:
        transformed = val * 3
        total_sum += transformed
        matched_count += 1

print(f"Pipeline Completed. Matched: {matched_count}, Total Sum: {total_sum}")
