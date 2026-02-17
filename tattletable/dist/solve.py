import sys

with open('decrypt.txt', 'r') as f:
    content = f.read()

result = []
for line in content.strip().split('\n'):
    parts = line.split()
    if not parts:
        continue
    # Skip the address (first field)
    for word in parts[1:]:
        try:
            val = int(word, 8)
            # od outputs 16-bit little-endian words
            b1 = val & 0xFF
            b2 = (val >> 8) & 0xFF
            if b1: result.append(chr(b1))
            if b2: result.append(chr(b2))
        except:
            pass

text = ''.join(result)
print(text)
