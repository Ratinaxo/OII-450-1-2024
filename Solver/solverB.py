import time
import numpy as np
import os
from Diversity.imports import diversidadHussain,porcentajesXLPXPT
from Metaheuristics.imports import iterarGWO,iterarPSA,iterarSCA,iterarWOA, iterarWOM
from Metaheuristics.imports import iterarPSO,iterarFOX,iterarEOO,iterarRSA,iterarGOA,iterarHBA,iterarTDO,iterarSHO
from Problem.Benchmark.Problem import fitness as f
from util import util
from BD.sqlite import BD
import random

def generarPoblacionInicial(pop, dim, lb, ub):
    # Initialize the positions of search agents
    population = np.zeros((pop, dim))
    for i in range(dim):
        population[:, i] = (
            np.random.uniform(0, 1, pop) * (ub[i] - lb[i]) + lb[i]
        )
    return population

def solverB(id, mh, maxIter, pop, function, lb, ub, dim):
    
    dirResult = './Resultados/'
    bd = BD()
    
    if not isinstance(lb, list):
        lb = [lb] * dim
    if not isinstance(ub, list):
        ub = [ub] * dim
    
    # tomo el tiempo inicial de la ejecucion
    initialTime = time.time()
    
    optimo = bd.obtenerOptimoInstancia(function)[0][0]
    if function == 'F8':
        optimo = optimo * dim
    initializationTime1 = time.time()
    
    results = open(dirResult+mh+"_"+function+"_"+str(id)+".csv", "w")
    results.write(
        f'iter,fitness,time,XPL,XPT,DIV\n'
    )
    
    vel = None
    pBestScore = None
    pBest = None
    
    if mh == 'PSO':
        vel = np.zeros((pop, dim))
        pBestScore = np.zeros(pop)
        pBestScore.fill(float("inf"))
        pBest = np.zeros((pop, dim))
    
    # Genero una población inicial 
    population = generarPoblacionInicial(pop, dim, lb, ub)
    
    maxDiversity = diversidadHussain(population)
    XPL , XPT, state = porcentajesXLPXPT(maxDiversity, maxDiversity)
    
    # Genero un vector donde almacenaré los fitness de cada individuo
    fitness = np.zeros(pop)

    # Genero un vetor dedonde tendré mis soluciones rankeadas
    solutionsRanking = np.zeros(pop)
    
    # calculo de factibilidad de cada individuo y calculo del fitness inicial
    for i in range(population.__len__()):
        for j in range(dim):
            population[i, j] = np.clip(population[i, j], lb[j], ub[j])            
        fitness[i] = f(function, population[i])
        if mh == 'PSO':
            if pBestScore[i] > fitness[i]:
                pBestScore[i] = fitness[i]
                pBest[i, :] = population[i, :].copy()
            
            
    
    solutionsRanking = np.argsort(fitness) # rankings de los mejores fitnes
    bestRowAux = solutionsRanking[0]
    # DETERMINO MI MEJOR SOLUCION Y LA GUARDO 
    best = population[bestRowAux].copy()
    bestFitness = fitness[bestRowAux]
    
    initializationTime2 = time.time()
    
    # mostramos nuestro fitness iniciales
    print("------------------------------------------------------------------------------------------------------")
    print(f"{function} {str(dim)} {mh} - best fitness inicial: {str(bestFitness)}")
    print("------------------------------------------------------------------------------------------------------")
    print("iter: "+
            str(0)+
            ", best: "+str(format(bestFitness,".2e"))+
            ", optimo: "+str(optimo)+
            ", time (s): "+str(round(initializationTime2-initializationTime1,3))+
            ", XPT: "+str(XPT)+
            ", XPL: "+str(XPL)+
            ", DIV: "+str(maxDiversity))
    results.write(
        f'0,{str(format(bestFitness,".2e"))},{str(round(initializationTime2-initializationTime1,3))},{str(XPL)},{str(XPT)},{str(maxDiversity)}\n'
    )

    # Función objetivo para GOA, HBA, TDO y SHO
    def fo(x):
        for j in range(x.__len__()): x[j] = np.clip(x[j], lb[j], ub[j]) # Reparación de soluciones
        return x,f(function,x) # Return de la solución reparada y valor de función objetivo
    
    for iter in range(0, maxIter):
        # obtengo mi tiempo inicial
        timerStart = time.time()
        
        # perturbo la population con la metaheuristica, pueden usar SCA y GWO
        # en las funciones internas tenemos los otros dos for, for de individuos y for de dimensiones
        try:
            if mh == "SCA":
                population = iterarSCA(maxIter, iter, dim, population.tolist(), best.tolist())
            if mh == "GWO":
                population = iterarGWO(maxIter, iter, dim, population.tolist(), fitness.tolist(), 'MIN')
            if mh == 'WOA':
                population = iterarWOA(maxIter, iter, dim, population.tolist(), best.tolist())
            if mh == 'PSA':
                population = iterarPSA(maxIter, iter, dim, population.tolist(), best.tolist())
            if mh == 'PSO':
                population, vel = iterarPSO(maxIter, iter, dim, population.tolist(), best.tolist(), pBest.tolist(), vel, ub[0])
            if mh == 'FOX':
                population = iterarFOX(maxIter, iter, dim, population.tolist(), best.tolist())
            if mh == 'EOO':
                population = iterarEOO(maxIter, iter, population.tolist(), best.tolist())
            if mh == 'RSA':
                population = iterarRSA(maxIter, iter, dim, population.tolist(), best.tolist(),lb[0],ub[0])
            if mh == 'GOA':
                population = iterarGOA(maxIter, iter, dim, population, best.tolist(), fitness.tolist(),fo, 'MIN')
            if mh == 'HBA':
                population = iterarHBA(maxIter, iter, dim, population.tolist(), best.tolist(), fitness.tolist(),fo, 'MIN')
            if mh == 'TDO':
                population = iterarTDO(maxIter, iter, dim, population.tolist(), fitness.tolist(),fo, 'MIN')
            if mh == 'SHO':
                population = iterarSHO(maxIter, iter, dim, population.tolist(), best.tolist(),fo, 'MIN')
            if mh == 'WOM':
                population = iterarWOM(maxIter, iter, dim, population.tolist(), fitness.tolist(), lb, ub, fo)
        except:
            exit(Exception("NO METAHEURISTIC FOUND"))
        finally:
            # calculo de factibilidad de cada individuo y calculo del fitness inicial
            for i in range(population.__len__()):
                for j in range(dim):
                    population[i, j] = np.clip(population[i, j], lb[j], ub[j])            
                fitness[i] = f(function, population[i])

                if mh == 'PSO':
                    if fitness[i] < pBestScore[i]:
                        pBest[i] = np.copy(population[i])
                
            solutionsRanking = np.argsort(fitness) # rankings de los mejores fitness
            
            #Conservo el best
            if fitness[solutionsRanking[0]] < bestFitness:
                bestFitness = fitness[solutionsRanking[0]]
                best = population[solutionsRanking[0]]

            div_t = diversidadHussain(population)

            if maxDiversity < div_t:
                maxDiversity = div_t
                
            XPL , XPT, state = porcentajesXLPXPT(div_t, maxDiversity)

            timerFinal = time.time()
            # calculo mi tiempo para la iteracion t
            timeEjecuted = timerFinal - timerStart
            
            if (iter+1) % (maxIter//4) == 0:
            # if (iter+1) % 10 == 0:
                print("iter: "+
                    str(iter+1)+
                    ", best: "+str(format(bestFitness,".2e"))+
                    ", optimo: "+str(optimo)+
                    ", time (s): "+str(round(timeEjecuted,3))+
                    ", XPT: "+str(XPT)+
                    ", XPL: "+str(XPL)+
                    ", DIV: "+str(div_t))
                    
            results.write(
                f'{iter+1},{str(format(bestFitness,".2e"))},{str(round(timeEjecuted,3))},{str(XPL)},{str(XPT)},{str(div_t)}\n'
            )
    finalTime = time.time()
    timeExecution = finalTime - initialTime
    print("------------------------------------------------------------------------------------------------------")
    print("Tiempo de ejecucion (s): "+str(timeExecution))
    print("best fitness: "+str(bestFitness))
    print("------------------------------------------------------------------------------------------------------")
    results.close()
    
    binary = util.convert_into_binary(dirResult+mh+"_"+function+"_"+str(id)+".csv")

    fileName = mh+"_"+function

    bd.insertarIteraciones(fileName, binary, id)
    bd.insertarResultados(bestFitness, timeExecution, best, id)
    bd.actualizarExperimento(id, 'terminado')
    
    os.remove(dirResult+mh+"_"+function+"_"+str(id)+".csv")