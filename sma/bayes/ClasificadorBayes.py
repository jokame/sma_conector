import redis
import re
import csv


class ClasificadorBayes(object):
    """docstring for Classifier"""
    def __init__(self, files):
        db = 0
        self.db = redis.StrictRedis(host='localhost', db=db)
        self.spl = re.compile("[\w\xe1\xe9\xed\xf3\xfa\xf1\xfc']+")

        while self.db.dbsize() != 0:
            db += 1
            self.db = redis.StrictRedis(host='localhost', db=db)
        self.train(files)

    def train(self, files):
        ColumnaTexto = 5
        ColumnaClase = 0
        with open(files, 'r') as archivo:
            listaCSV = csv.reader(archivo)
            for lineCSV in listaCSV:
                lines = self.spl.findall(lineCSV[ColumnaTexto].lower())
                clase = lineCSV[ColumnaClase]
                linea = set(lines)
                for word in linea:
                    if len(word) > 1:
                        self.db.hincrby(word, '.'+clase)
                        self.db.hincrby(word, '-total')
                self.db.hincrby('.-'+clase, 'ccont')
                self.db.incr('.totalitems')
            archivo.close()
        print 'datos cargados'
        clases = self.db.keys(pattern='.-*')
        self.clases = [clase[2:] for clase in clases]
        for clase in self.clases:
            self.setcprob(clase)
        features = self.db.keys()
        for feature in features:
            if feature[0] != '.':
                for clase in self.clases:
                    self.setfprob(feature, clase)

    def setcprob(self, clase):
        ccont = float(self.db.hget('.-'+clase, 'ccont'))
        totalitems = float(self.db.get('.totalitems'))
        lprob = ccont/totalitems
        self.db.hset('.-'+clase, 'cprob', lprob)

    def getcprob(self, clase):
        return float(self.db.hget('.-'+clase, 'cprob'))

    def setfprob(self, feature, clase, peso=1, probi=0.5):
        ccont = float(self.db.hget('.-'+clase, 'ccont'))
        total = float(self.db.hget(feature, '-total'))
        if self.db.hexists(feature, '.'+clase):
            featurecont = float(self.db.hget(feature, '.'+clase))
        else:
            featurecont = 0
        prob = ((featurecont*total)/ccont+peso*probi)/(total+peso)
        self.db.hset(feature, clase, prob)

    def getfprob(self, feature, clase):
        return float(self.db.hget(feature, clase))

    def clasifica(self, text):
        labels = dict([(clase, 0) for clase in self.clases])
        features = [feature for feature in self.spl.findall(text.lower()) if len(feature) > 1]
        features = set(features)
        for feature in features:
            if self.db.exists(feature):
                for label in labels:
                    if labels[label] != 0:
                        labels[label] *= self.getfprob(feature, label)
                    else:
                        labels[label] = self.getfprob(feature, label)

        for label in labels:
            cprob = self.getcprob(label)
            labels[label] *= cprob

        slebal = [(lbl, labels[lbl]) for lbl in labels]
        slebal.sort(self.sortea)
        if slebal[0][1] > slebal[1][1]:
            clase = slebal[0][0]
        else:
            clase = 'indefinido'
        return (text, clase)

    def exporttrain(self, files):
        with open(files, 'w+') as backup:
            for clase in self.clases:
                backups = 'clase|'+clase+'|'+self.db.hget('.-'+clase, 'cprob')+'\n'
                backup.write(backups)

            features = [feature for feature in self.db.keys(pattern='*') if feature[0] != '.']
            for feature in features:
                backups = 'feature|'+feature+'|'
                for clase in self.clases:
                    backups = backups+self.db.hget(feature, clase)+'|'
                backups = (backups+'\n')
                #.encode('utf-8')
                backup.write(backups)
            backup.close()

    def exporttraintoC(self, files):
        with open(files, 'w+') as backup:
            features = [feat for feat in self.db.keys() if feat[0] != '.']
            features.sort()
            backups = '#define NUMCLASES '+str(len(self.clases))+'\n'
            backups += '#define NUMFEATURES '+str(len(features))+'\n'
            backups += 'struct labels{float prob; \n char *label;\n } clases [NUMCLASES]={'
            backup.write(backups)
            backups = ''
            for clase in self.clases:
                backups += '{'+self.db.hget('.-'+clase, 'cprob')+'f,"'+clase+'"},'
            backups = backups[:-1]+'};\n typedef struct labels clasestipo;\n'
            backup.write(backups)

            backups = 'clasestipo probclases[NUMCLASES]={'
            backup.write(backups)
            backups = ''
            for clase in self.clases:
                backups += '{0.0f,"'+clase+'"},'
            backups = backups[:-1]+'};\n'
            backup.write(backups)

            backups = 'struct feature{\nchar *feature;\nfloat probabilidades[NUMCLASES];\n} features[NUMFEATURES]={'
            for feature in features:
                backups += '{"'+feature+'",{'
                for clase in self.clases:
                    backups += self.db.hget(feature, clase)+'f,'

                backups = backups[:-1]+'}},'
            backups = backups[:-1]+'};\n typedef struct feature featuretipo; '

            backup.write(backups)
            backup.close()

    def sortea(self, a, b):
        if a[1] > b[1]:
            rst = -1
        elif a[1] < b[1]:
            rst = 1
        else:
            rst = 0
        return rst


def main():
    clasi = ClasificadorBayes('TweetsdeEntrenamiento.csv')
    print clasi.clasifica('chancho de plata')
    print clasi.clasifica('no quiero trabajar')
    print clasi.clasifica('hermoso')
    print clasi.clasifica('esta horrible no')
    print clasi.clasifica('no pasaras examen')
   # clasi.exporttraintoC('entrenadorC.txt')
    clasi.db.flushdb()


if __name__ == '__main__':
    main()
