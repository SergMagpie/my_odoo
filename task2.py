def draw_a_pyramid(input_string: str) -> str:
    '''The function returns a pyramid of the given characters 
    and the given height, entered with a space.'''
    symbol, number = input_string.split(' ')
    number = int(number)
    string = ''
    for i in range(1, number + 1):
        string += ' ' * (number - i) + symbol * (i * 2 - 1) + '\n'
    return str(len(string) - number) + '\n' + string


if __name__ == '__main__':
    print(draw_a_pyramid(input()))
