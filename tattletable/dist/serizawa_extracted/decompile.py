import marshal, dis

with open("serizawa.pyc","rb") as f:
    f.read(16)
    code = marshal.load(f)

dis.dis(code)
