
# a = 0
# b = 1

# answers = [1, 0, 0, 3, 2, 0, 4, 3, 0, 0, 0, 0, 3, 4, 3, 0, 0, 4, 3, 4, 0, 0, 0, 0, 0, 0]
# test = []

# for i in range(26):
#     test.append(a % 6 + 1)

#     a, b = a + b, a
# print(answers)
# print(test)

chars = ". y . i . n . s . i . c".split(" ")


def get_number_tuples(number):
    tups = set()
    for i in range(number):
        tups.add((chr(number - i - 1 + 97), chr(i + 97)))
    
    for i in range(number, number + 26):
        tups.add((chr((number + 26 - i - 1) % 26 + 97), chr(i % 26 + 97)))
    
    return tups

import time
def fill(i, total):
    if len(total) == len(chars):
        if not True in [letter in ['x', 'y', 'q'] for letter in total]:
            print(total + ['a', 'n', 'd'])
            time.sleep(.01)

        return # exit cond

    char = chars[i]
    if char != ".":
        num = ord(char) - 97

        to_test = get_number_tuples(num)
        for a, b in to_test: # Split character
            new_total = total.copy()
            new_total.append(a)
            new_total.append(b)
            fill(i + 2, new_total)


# for char in chars:
#     if char == ".":
#         continue
    
#     num = ord(char) - 97
#     print(get_number_tuples(num))

# fill(1, [])

# KI  
# SA
# OE
# AS 
# IK 
# BR



# fill(1, []) # Start one off


# Wat zijn a en b?(2)
# 4, 4, 4, 4, 4, a, 5, 3, 3, 7, 3, 
# 3, 2, 7, 5, 6, 4, 7, 7, b, 2, 2, 
# 3, 2, 1, 7, 7, 1, 1, 2, 2, 5, 5.

a = [4, 4, 4, 4, 4, 0, 5, 3, 3, 7, 3]
b = [3, 2, 7, 5, 6, 4, 7, 7, 0, 2, 2]
c = [3, 2, 1, 7, 7, 1, 1, 2, 2, 5, 5]
print(sum(a), sum(b), sum(c))


nums = [9, 11, 14, 15, 21, 23, 26, 29, 32, 37, 38, 40, 44, 45, 47, 50, 52, 53, 56, 59, 62, 63, 64, 67, 68, 69, 71, 75, 76,
81, 82, 83, 86, 88, 92, 94, 97, 99, 101, 105, 111, 112, 116, 127, 128, 131, 134, 136, 140, 149, 153, 157, 158, 160,
163, 164, 167, 171, 172, 173, 177, 179, 182, 183, 189, 191, 194, 197, 200, 211, 212, 223, 225, 226, 227, 231, 232,
236, 239, 242, 251, 254, 255, 256, 257, 261, 263, 266, 268, 269, 273, 279, 280]

print([nums[i] - nums[i - 1] for i in range(1, len(nums))])

a = "bkafxipth"
b = "frcbveugy"
c = "lxqdjzpma"
print(sum([ord(n)-97 for n in a]))
print(sum([ord(n)-97 for n in b]))
print(sum([ord(n)-97 for n in c]))

# * _ e | f r c | h o *
# j * m | b v e | k * s
# z i * | u g y | * q n
# ---------------------
# b k a | * w * | c d y
# f x i | h * l | u e r
# p t h | * o * | n g _
# ---------------------
# o n * | l x q | * j w
# c * g | d j z | b * u
# * y _ | p m a | t s *


#   7 2 5 | 6 9 3 | 8 1 4
#   8 1 6 | 2 4 5 | 7 9 3
#   9 4 3 | 1 7 8 | 5 2 6
#   ------|-------|------
#   2 7 1 | 9 5 6 | 3 4 8
#   6 3 4 | 8 2 7 | 1 5 9
#   5 9 8 | 3 1 4 | 6 7 2
#   ------|-------|------
#   1 6 9 | 7 3 2 | 4 8 5
#   3 5 7 | 4 8 9 | 2 6 1
#   4 8 2 | 5 6 1 | 9 3 7

# 0,0 : a d g h k l n q s t u v w z y 

# Indices
# a b c d e f g h i j 
# 0 1 2 3 4 5 6 7 8 9 

# k l m n o p q r s t 
# 0 1 2 3 4 5 6 7 8 9

# u v w x y z
# 0 1 2 3 4 5

class Sudoku:
    letters = [None] * 26
    rules = [
        [ord(l) - 97 for l in "efrcho"],
        [ord(l) - 97 for l in "jmbveks"],
        [ord(l) - 97 for l in "ziugyqn"],
        [ord(l) - 97 for l in "bkawcdy"],
        [ord(l) - 97 for l in "fxihlue"],
        [ord(l) - 97 for l in "pthong"],
        [ord(l) - 97 for l in "onlxqjw"],
        [ord(l) - 97 for l in "cgdjzbu"],
        [ord(l) - 97 for l in "ypmats"],

        [9, 25, 2, 5, 15, 14, 3],
        [8, 10, 23, 19, 13, 24],
        [4, 12, 0, 8, 7, 6],
        [5, 1, 20, 7, 11, 3, 15],
        [17, 21, 6, 22, 14, 23, 9, 12],
        [2, 4, 24, 11, 16, 25, 0],
        [7, 10, 2, 20, 13, 1, 19],
        [14, 16, 3, 4, 6, 9, 18],
        [18, 13, 24, 17, 22, 20],

        [4, 9, 12, 25, 8],
        [5, 17, 2, 1, 21, 4, 20, 6, 24],
        [7, 14, 10, 18, 16, 13],
        [1, 10, 0, 5, 23, 8, 15, 19, 7],
        [23, 7, 11, 14],
        [2, 3, 24, 20, 4, 17, 13, 6],
        [14, 13, 2, 6, 24],
        [11, 23, 16, 3, 9, 25, 15, 12, 0],
        [9, 22, 1, 20, 19, 18]
    ]

    def gen_letters(self, i):
        if i == 26:
            return False

        for j in range(1, 10):
            if i == 0:
                print(j)
            
            self.letters[i] = j
            correct = False

            valid_set = self.test()
            if valid_set:
                if i == 25: # Exit condition if the last letter is also valid
                    print(self.letters)
                    return False
                # Check for the next letter
                correct = self.gen_letters(i + 1)

            if correct: # Exit if the recusive function had a valid result
                return True

        # Reset value to original
        self.letters[i] = None
        return False
            
    def start_gen_test(self):
        i = 0
        for j in range(1, 10):
            print(j)
            
            self.letters[i] = j
            correct = False

            valid_set = self.test()
            if valid_set:
                if i == 26: # Exit condition if the last letter is also valid

                    return True
                # Check for the next letter
                correct = self.gen_letters(i + 1)

            if correct: # Exit if the recusive function had a valid result
                return True

        # Reset value to original
        self.letters[i] = None
        return False


    def test(self):
        # s = square, c = column, r = row
        for rule in self.rules:
            nums = [self.letters[i] for i in rule if self.letters[i] is not None]
            if len(nums) != len(set(nums)):
                return False
        
        return True

sud = Sudoku()

sud.start_gen_test()









