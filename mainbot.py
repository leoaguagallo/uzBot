
import numpy
import tflearn 
import tensorflow
import nltk
from nltk.stem.lancaster import LancasterStemmer
import json
import random
import pickle
import discord

key = 'su key aqui'
#nltk.download('punkt') #al inicio de la compilacion

#instanciacion de la clase
stemmer = LancasterStemmer()

# extracion de datos del json
with open('question.json', encoding = 'utf-8') as questions:
    data = json.load(questions)

try:
    # si existe datos de entrenamiento abrir en modo lectura
    with open('trainig_data.pickle', 'rb') as pickle_file:
        #inicializar variables con datos
        words, tags, training, out = pickle.load(pickle_file)
except:

    words = []
    tags = []
    aux_x = [] # aux_word
    aux_y = [] # aux_tags

    # recorre los datos del json
    for q in data["question"]:
        for clue in q["patrones"]:
            auxWord = nltk.word_tokenize(clue)  #separa palabras

            words.extend(auxWord)  #agregamos todas las palabras
            aux_x.append(auxWord) #agregamos la frase
            aux_y.append(q["tag"]) #agregamos el tag

            if q["tag"] not in tags: #no se repitan el tag
                tags.append(q["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"] #conversion de palabras a minusculas
    words = sorted(list(set(words))) # ordenar palabras
    tags = sorted(tags)

    training = []
    out = []
    empty_out = [ 0 for _ in range(len(tags))] # salida vacia oon diemension de tags

    for indice, objectWord in enumerate(aux_x):
        cubeta = []
        aux_wd = [stemmer.stem(w.lower()) for w in objectWord]

        for w in words:
            if w in aux_wd:
                cubeta.append(1)
            else:
                cubeta.append(0)

        row_out = empty_out[:]
        row_out[tags.index(aux_y[indice])] = 1
        training.append(cubeta)
        out.append(row_out)

    training = numpy.array(training) # conversion a arreglos numpy
    out = numpy.array(out)

    # guardar datos de entrenamiento en modo escritura
    with open('trainig_data.pickle', 'wb') as pickle_file:
        pickle.dump((words, tags, training, out), pickle_file)

tensorflow.reset_default_graph() # reseteo de red

net = tflearn.input_data(shape = [None, len(training[0])]) # capa de entrada
net = tflearn.fully_connected(net, 10) #capaas ocultas
net = tflearn.fully_connected(net, 10)
net = tflearn.fully_connected(net, len(out[0]), activation = "softmax") #capa de salida
net = tflearn.regression(net) #algoritmo de entrenamiento

model = tflearn.DNN(net)

try:
    #si existe el modelo lo cargamos
    model.load('model.tflearn')
except:
    #entrenar el modelo
    model.fit(training, out, n_epoch = 100, batch_size = 10, show_metric = True)
    #guardar el modelo
    model.save("model.tflearn")

def mainBot():

    #discord key
    global key
    #abrir conexion a discord
    conx = discord.Client()

    while True:

        # evento de discord
        @conx.event
        async def on_message(msg):

            # para que no recoosca respuestas del bot 
            # solo del usuario
            if msg.author == conx.user: 
                return

            #inputs = input("User: ")
            cubeta = [ 0 for _ in range(len(words))]
            #process_input = nltk.word_tokenize(inputs)
            process_input = nltk.word_tokenize(msg.content)
            process_input = [stemmer.stem(word.lower()) for word in process_input]

            for one_word in process_input:
                for indice, word in enumerate(words):
                    if word == one_word:
                        cubeta[indice] = 1

            res = model.predict([numpy.array(cubeta)])
            index_res = numpy.argmax(res)
            tag = tags[index_res]

            for aux_tag in data["question"]:
                if aux_tag["tag"] == tag:
                    answer = aux_tag["respuestas"]

            #print("Uzbot: ", random.choice(answer))
            # envio de respuesta a discord  
            await msg.channel.send(random.choice(answer))

        #correr discord
        conx.run(key)

mainBot()
