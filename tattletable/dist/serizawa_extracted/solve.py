import struct

FORMAT = "QQHHi"
EVENT_SIZE = struct.calcsize(FORMAT)

KEY_MAP = {
    2:'1',3:'2',4:'3',5:'4',6:'5',
    7:'6',8:'7',9:'8',10:'9',11:'0',
    12:'-', 13:'=',
    16:'q',17:'w',18:'e',19:'r',20:'t',
    21:'y',22:'u',23:'i',24:'o',25:'p',
    30:'a',31:'s',32:'d',33:'f',34:'g',
    35:'h',36:'j',37:'k',38:'l',
    39:';', 40:"'",
    44:'z',45:'x',46:'c',47:'v',
    48:'b',49:'n',50:'m',
    52:'.', 53:'/',
    57:' ', 28:'\n'
}

SHIFT_MAP = {
    12:'_', 13:'+',
    39:':', 40:'"',
    52:'>', 53:'?',
}

output = []
shift_pressed = False
caps_lock = False

with open("cron.aseng", "rb") as f:
    while True:
        data = f.read(EVENT_SIZE)
        if not data:
            break
        tv_sec, tv_usec, type_, code, value = struct.unpack(FORMAT, data)
        
        if type_ == 1 and value == 1:  # Key press
            if code == 42:  # SHIFT
                shift_pressed = True
            elif code == 58:  # CAPSLOCK
                caps_lock = not caps_lock
            elif code == 14:  # BACKSPACE
                if output:
                    output.pop()
            elif code == 29:  # CTRL
                pass
            else:
                char = None
                if shift_pressed and code in SHIFT_MAP:
                    char = SHIFT_MAP[code]
                elif code in KEY_MAP:
                    char = KEY_MAP[code]
                
                if char:
                    # Apply caps lock to letters
                    if caps_lock and char.isalpha():
                        char = char.upper()
                    output.append(char)
                
                shift_pressed = False

print(''.join(output))
