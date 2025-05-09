import json
from pathlib import Path

input_file = Path('../data/raw/ei_2019_12_31.json')
output_dir = Path('../data/split/')
output_dir.mkdir(parents=True, exist_ok=True)

#loads full data
with open(input_file, 'r', encoding='utf8') as f:
    data = json.load(f)

#finding midpoint
mindpoint = len(data) // 2
first_half = data[:mindpoint]
second_half = data[mindpoint:]

#write first half
with open(output_dir / 'ei_2019_12_31_part1.json', 'w', encoding='utf-8') as f:
    json.dump(first_half, f, ensure_ascii=False, indent=4)

#write second half
with open(output_dir / 'ei_2019_12_31_part2.json', 'w', encoding='utf-8') as f:
    json.dump(second_half, f, ensure_ascii=False, indent=4)