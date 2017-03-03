import csv

NUM_JUDGES = 1
PROJECTS_CSV = 'hackillinois.csv'
csv_encoding = 'iso-8859-1'

mappings = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
NUM_LETTERS = 14


f = open(PROJECTS_CSV, encoding=csv_encoding, newline='')
c = csv.reader(f)
NUM_PROJECTS = 0
for row in c:
    NUM_PROJECTS += 1
NUM_PROJECTS -= 1

PROJECTS_PER_JUDGE = 117

f.seek(0,0)
next(c)
print(NUM_PROJECTS)
ij = 0

def convert_number_to_table(number):
    letter = int(number / 6)
    let_num = number % 6

    letter = mappings[letter]
    return str(letter) + str(let_num+1)


for i in range(NUM_JUDGES):
    j = open('{}.txt'.format(i), mode='w+')
    for k in range(ij, ij + PROJECTS_PER_JUDGE):
        try:
            proj_name = next(c)[0]
        except StopIteration:
            f.seek(0,0)
            next(c)
            proj_name = next(c)[0]
        table_map = convert_number_to_table(k%117)
        print('{}'.format(table_map), file=j)
    ij += PROJECTS_PER_JUDGE

j.truncate()


