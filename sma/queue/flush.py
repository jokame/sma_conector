import sys
import time
import redis
import csv
import locale
import ast


def writeVec(path, vec):
    language, output_encoding = locale.getdefaultlocale()
    with open(path, 'w') as f:
        if vec != []:
            write = csv.writer(f, delimiter='|')
            write.writerow([w.encode(output_encoding) for w in vec])
    f.close()


def writeSingle(path, vec):
    language, output_encoding = locale.getdefaultlocale()
    with open(path, 'w') as f:
        if vec != "":
            f.write(vec.encode(output_encoding))
    f.close()


def flush(t, db, path):
    r = redis.StrictRedis('localhost')

    while True:
        if r.lindex(db, 0) is not None:
            w = r.lpop(db)

            try:
                w = ast.literal_eval(w)
                writeVec(path, w)
            except Exception:
                writeSingle(path, w)

            print w
        else:
            time.sleep(0.1)
            f = open(path, 'w')
            f.write("")
            f.close()

        time.sleep(float(t))


if __name__ == '__main__':
    flush(sys.argv[1], sys.argv[2], sys.argv[3])
