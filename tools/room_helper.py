"""

HELPER FILE TO CREATE ROOM LAYOUTS

Formatting room layouts:
" ": no room
".": room
"q": end layout (place in a single line)

Example:

   ..
   .
......
 . .
 ....
q

"""

print("Paste your room layout (multi-line).")
layout = []
y = 0
while True:
    layout_line = input("> ")
    if layout_line == "q":
        break
    else:
        for x, character in enumerate(layout_line):
            if character == ".":
                layout.append(f"{x},{y}")
    y += 1
print("RESULT:")
for index, item in enumerate(layout):
    if index == len(layout) - 1:
        print(f"\"{item}\": {{}}")
    else:
        print(f"\"{item}\": {{}},")