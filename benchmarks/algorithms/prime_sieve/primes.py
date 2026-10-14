def count_primes(limit: int) -> int:
    count = 0
    for n in range(2, limit + 1):
        is_prime = True
        d = 2
        while d * d <= n:
            if n % d == 0:
                is_prime = False
                break
            d += 1
        if is_prime:
            count += 1
    return count

if __name__ == '__main__':
    total = count_primes(10000)
    print(f"Primes count up to 10000: {total}")
