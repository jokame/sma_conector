import ClasificadorBayes
import csv
import numpy
#import matplotlib.pyplot as ply

ColumnaTexto = 1
ColumnaClase = 0


def varparametros(filename, inicio, fin, paso):
    resultados = []
    x = []
    y = []
    probis = numpy.arange(inicio, fin, paso)
    for probi in probis:
        resultado = (probi, Probador(filename, peso=1, probi=probi))
        resultados.append(resultado)
        x.append(resultado[0])
        y.append(resultado[1])
    respaldo = open('resultados2.txt', 'w')
    for res in resultados:
        cadena = str(res[0]) + '    ' + str(res[1]) + '\n'
        respaldo.write(cadena)
    respaldo.close()
#   ply.plot(x,y,'r*-')
#   ply.show()
    return resultados


def Probador(filename, peso=1, probi=0.5):
    aciertos = 0.0
    totales = 0.0
    db_clasificador = 1
    clasi = ClasificadorBayes.ClasificadorBayes()
    clasi.loadFromRedis(db_clasificador)
    archivo = open(filename, 'r')
    csvlector = csv.reader(archivo)
    for linea in csvlector:
        texto = linea[ColumnaTexto]
        clase = linea[ColumnaClase]
        if clase in clasi.clases:
            clasi.setfprobs(texto, peso=peso, probi=probi)
            (a, claseclasif) = clasi.clasifica(texto)
            if claseclasif == clase:
                aciertos += 1
            totales += 1
            if totales % 500 == 0:
                print totales
    archivo.close()
    eficacia = (aciertos * 100) / totales
    print 'Precision de ' + str(eficacia) + '% para ' + str(probi) + ' aciertos: ' + str(aciertos) + ', total de: ' + str(totales)
    return eficacia
