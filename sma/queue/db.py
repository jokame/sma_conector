import redis
import subprocess


class DB(object):
    def __init__(self, id, path):
        self.id = id
        self.r = redis.StrictRedis(host='localhost')
        self.path = path

    def sink(self, val):
        self.r.rpush(self.id, val)

    def flushDB(self, t):
        subprocess.Popen(["python",
                         "../sma_conector/sma/queue/flush.py",
                         str(t), self.id, self.path],
                         #shell=True)
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
