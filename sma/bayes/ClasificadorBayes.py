import redis
import re
import csv


class ClasificadorBayes(object):
    """docstring for Classifier"""
    def __init__(self, files=None):
        db = 0
        self.db = redis.StrictRedis(host='localhost', db=db)
        self.spl = re.compile("[\w\xe1\xe9\xed\xf3\xfa\xf1\xfc']+")
        self.dict = {}

        while self.db.dbsize() != 0:
            db += 1
            self.db = redis.StrictRedis(host='localhost', db=db)
        if files is not None:
            self.ConteoTrain(files)

    def setProbsInd(self, Individuo, featurelist):
        parametros = Individuo[1]
        contador = 1
        for feature in featurelist:
            for clase in self.clases:
                self.setfprob(feature, clase, peso=parametros[0], probi=parametros[contador])
            contador += 1

    def ConteoTrain(self, files):
        ColumnaTexto = 1
        ColumnaClase = 0
        contador = 0
        with open(files, 'r') as archivo:
            listaCSV = csv.reader(archivo)
            for lineCSV in listaCSV:
                contador += 1
                if contador % 100 == 0:
                    print contador
                lines = self.spl.findall(lineCSV[ColumnaTexto].lower())
                clase = lineCSV[ColumnaClase]
                linea = set(lines)
                print contador
                for word in linea:
                    if len(word) > 1:
                        self.db.hincrby(word, '.'+clase)
                        self.db.hincrby(word, '-total')
                self.db.hincrby('.-'+clase, 'ccont')
                self.db.incr('.totalitems')
            archivo.close()

    def setprobs(self, peso=1, probi=0.5):
        clases = self.db.keys(pattern='.-*')
        self.clases = [clase[2:] for clase in clases]
        for clase in self.clases:
            self.setcprob(clase)
        features = [key for key in self.db.keys() if key[0] != '.' and key[0] != '-']
        numfeatures = len(features)
        contador = 0
        for feature in features:
            contador += 1
            if contador % (numfeatures/100) == 0:
                print str((100*contador)/numfeatures)+'% calculado para probi ='+str(probi)
            for clase in self.clases:
                self.setfprob(feature, clase, peso=peso, probi=probi)

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

    def getfprobcustom(self, feature, clase, peso=1, probi=0.5):
        ccont = float(self.db.hget('.-'+clase, 'ccont'))
        total = float(self.db.hget(feature, '-total'))
        if self.db.hexists(feature, '.'+clase):
            featurecont = float(self.db.hget(feature, '.'+clase))
        else:
            featurecont = 0
        prob = ((featurecont*total)/ccont+peso*probi)/(total+peso)
        return prob

    def getfprob(self, feature, clase):
        return float(self.db.hget(feature, clase))

    def setfprobs(self, text, peso=1, probi=0.5):
        features = [feature for feature in self.spl.findall(text.lower()) if len(feature) > 1]
        features = set(features)
        for feature in features:
            if self.db.exists(feature):
                for clase in self.clases:
                    self.setfprob(feature, clase, peso=peso, probi=probi)

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
            for feature in features[:-1]:
                backups += '{"'+feature+'",{'
                for clase in self.clases[:-1]:
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

    def loadFromRedis(self, db=0):
        self.db = redis.StrictRedis(host='localhost', db=db)
        clases = self.db.keys(pattern='.-*')
        self.clases = [clase[2:] for clase in clases]


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
