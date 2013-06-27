import csv
import ClasificadorBayes
import re
import random
import pickle

ColumnaTexto = 5
ColumnaClase = 0


def ProbadorGenetico(filename, NumdeIndividuos, iteraciones):
    if NumdeIndividuos % 4 != 0:
        print 'Numero de individuos debe ser multiplo de 4'
        return []
    db_clasificador = 0
    clasi = ClasificadorBayes.ClasificadorBayes()
    clasi.loadFromRedis(db_clasificador)
    (Individuos, featurelist) = generaIndividuos(clasi, filename, NumdeIndividuos)
    PickleFeaturelistFile = open('FeatureList.pickle', 'w')
    pickle.dump(featurelist, PickleFeaturelistFile)
    PickleFeaturelistFile.close()
    contadoriteraciones = 0
    while contadoriteraciones <= iteraciones:
        contadordepruebas = 1
        for individuo in Individuos:
            if individuo[0] == 0:
                resultado = PruebaGenetico(clasi, filename, individuo, featurelist)
                individuo[0] = resultado
            print 'prueba:' + str(contadordepruebas) + ',	iteracion:' + str(contadoriteraciones) + ' eficacia de ' + str(individuo[0])
            contadordepruebas += 1
        Individuos.sort()
        Individuos.reverse()
        backup = file('IndividuosIt-' + str(contadoriteraciones) + '.pickle', 'w')
        pickle.dump(Individuos, backup)
        backup.close()
        if contadoriteraciones != iteraciones:
            for pareja in range(1, (NumdeIndividuos / 4) + 1):
                cruza(pareja, NumdeIndividuos, Individuos)
        contadoriteraciones += 1
        backup = file('IndividuosGanadores.pickle', 'w')
        pickle.dump(Individuos, backup)
        backup.close()


def cruza(pareja, NumdeIndividuos, Individuos):
    indexma = pareja*2-2
    indexpa = pareja*2-1
    indexhijo1 = indexma + NumdeIndividuos/2
    indexhijo2 = indexpa + NumdeIndividuos/2
    Padre = Individuos[indexpa]
    Madre = Individuos[indexma]
    Hijo1 = Individuos[indexhijo1]
    Hijo2 = Individuos[indexhijo2]
    ParamMadre = Madre[1]
    ParamPadre = Padre[1]
    ParamHijo1 = Hijo1[1]
    ParamHijo2 = Hijo2[1]
    Hijo1[0] = 0
    Hijo2[0] = 0
    NumParam = len(ParamMadre)
    for param in range(0, NumParam):
        volado = random.random()
        if volado < 0.5:
            ParamHijo1[param] = ParamMadre[param]
            ParamHijo2[param] = ParamPadre[param]
        if volado >= 0.5:
            ParamHijo2[param] = ParamMadre[param]
            ParamHijo1[param] = ParamPadre[param]


def generaIndividuos(clasi, filename, NumeroDeIndividuos):
    split = re.compile("[\w\xe1\xe9\xed\xf3\xfa\xf1\xfc']+")
    archivo = open(filename, 'r')
    rediskeys = clasi.db.keys()
    print 'keys leidas'
    keys = [key for key in rediskeys if key[0] != '.' and key[0] != '-']
    csvreader = csv.reader(archivo)
    features = set([])
    for linea in csvreader:
        texto = linea[ColumnaTexto]
        texto = texto.lower()
        featuresTexto = split.findall(texto)
        for feat in featuresTexto:
            features.add(feat)
    NumFeatures = len(features)
    archivo.close()
    featurelist = [feature for feature in features if feature in keys]
    featurelist.sort()
    Individuos = []
    for contador in range(1, NumeroDeIndividuos+1):
        Individuo = generaInd(NumFeatures)
        Individuos.append(Individuo)
    return (Individuos, featurelist)


def generaInd(NumPesos):
    Individuo = [0]
    Individuo2 = [random.random()]
    for cont in range(1, NumPesos+1):
        Individuo2.append(random.random())
    Individuo.append(Individuo2)
    return Individuo


def setProbsInd(Clasificador, Individuo, featurelist):
    parametros = Individuo[1]
    contador = 1
    for feature in featurelist:
        for clase in Clasificador.clases:
            Clasificador.setfprob(feature, clase, peso=parametros[0], probi=parametros[contador])
        contador += 1


def PruebaGenetico(clasi, filename, Individuo, featurelist):
    aciertos = 0.0
    totales = 0.0
    setProbsInd(clasi, Individuo, featurelist)
    archivo = open(filename, 'r')
    csvlector = csv.reader(archivo)
    for linea in csvlector:
        texto = linea[ColumnaTexto]
        clase = linea[ColumnaClase]
        if clase in clasi.clases:
            (a, claseclasif) = clasi.clasifica(texto)
            if claseclasif == clase:
                aciertos += 1
            totales += 1
    archivo.close()
    eficacia = (aciertos*100)/totales
    return eficacia


def main():
    ProbadorGenetico('testdata.manual.2009.06.14.csv', 40, 2)

if __name__ == '__main__':
    main()
