def count_vowels(input_sring: str) -> int:
    '''The function returns the number of 
    vowel characters in a string.'''
    counter = 0
    for i in input_sring:
        if i in ('AEIOUY'):
            counter += 1
    return counter


if __name__ == '__main__':
    print(count_vowels(input()))
