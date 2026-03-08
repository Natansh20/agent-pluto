import sys

def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def list_primes_up_to(n):
    primes = [i for i in range(2, n+1) if is_prime(i)]
    return primes

def main(arg):
    number = int(arg)
    if is_prime(number):
        print(f'{number} is a prime number. Primes up to {number}:', list_primes_up_to(number))
    else:
        print(f'{number} is not a prime number.')

if __name__ == '__main__':
    main(sys.argv[1])