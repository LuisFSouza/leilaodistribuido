from flask import Flask, request, render_template
import redis;
import json;
from flask_socketio import SocketIO, join_room
import threading
from redis_lock import RedisLock
from datetime import datetime
import uuid

id_server = uuid.uuid4()

app = Flask(__name__)

redisPubSub = redis.StrictRedis(host='redis-pub-sub', port=6379, db=0, decode_responses=True)

socket = SocketIO(app, cors_allowed_origins="*")

#Room de leilão
@socket.on('join-room-leilao')
def joinLeilao(dados):
    leilao = dados.get('leilao')
    join_room(int(leilao))

#Room de leilões
@socket.on('join-room-leiloes')
def joinLeilao():
    join_room('leiloes')


def redisSub():
    pubsubRedis = redisPubSub.pubsub();
    #Se inscrevendo nos eventos de interesse
    pubsubRedis.subscribe(['novo_lance', 'novo_leilao', 'leilao_expirado', '__keyevent@0__:expired'])

    for mensagem in pubsubRedis.listen():
        if mensagem['type'] == 'message':
            canalEnvio = mensagem['channel'];
            #Evento de leilão expirou ou vai expirar
            if(canalEnvio == '__keyevent@0__:expired'):
                #Evento de leilão vai expirar em 30 segundos
                if (mensagem['data']).startswith('leilaoaviso'):
                    leilao = mensagem['data'].split("-")[1]
                    #Envia tanto para a tela de leilões quanto para a tela de visualização de leilão o acontecimento, passando o id do leilão que vai expirar
                    socket.emit("leilao_vai_expirar", leilao, room='leiloes')
                    socket.emit("leilao_vai_expirar", leilao, room=int(leilao))
                else:
                    #Evento de leilão expirou
                    leilao = mensagem['data'].split("-")[1]
                    #Envia tanto para a tela de leilões quanto para a tela de visualização de leilão o acontecimento, passando o id do leilão que expirou
                    socket.emit("leilao_expirado", leilao, room='leiloes')
                    socket.emit("leilao_expirado", leilao, room=int(leilao))
            else:
                dadosMensagem = json.loads(mensagem['data']);
                #Evento de novo lance no leilão
                if(canalEnvio == 'novo_lance'):
                     #Envia tanto para a tela de leilões quanto para a tela de visualização de leilão o acontecimento, passando as informações do novo lance
                    socket.emit("atualizacao_lances", dadosMensagem, room=int(dadosMensagem['leilao']))
                    socket.emit("atualizacao_lances", dadosMensagem, room='leiloes')
                #Evento de novo leilão
                elif(canalEnvio == 'novo_leilao'):
                    #Envia para a tela de leilões o acontecimento, passando as informações do novo leilão
                    socket.emit("atualizacao_leilao", dadosMensagem, room='leiloes')
               
threading.Thread(target=redisSub, daemon=True).start()

@app.route('/create-auction', methods=['POST'])
def createAuction():
    print("Criação de leilão na instância de ID: " + str(id_server))
    #Pega as informações do leilão
    dados = request.get_json()
    titulo = dados.get('titulo')
    descricao = dados.get('descricao')
    precoInicial = None
    #Verificando se o preço é um numero
    try:
        precoInicial = float(dados.get('precoinicial'))
    except: 
        return "O valor inicial do lance tem que ser um número", 400 

    horarioTermino = dados.get('horariotermino')

    agora = datetime.now()
    horarioTerminof = None

    #Verifica se a data esta no formato correto
    try:
        horarioTerminof = datetime.fromisoformat(horarioTermino).replace(second=0, microsecond= 0)
    except: 
        return "A data tem que estar no formato ISO 8601", 400
        
    diff = horarioTerminof - agora

    #Verifica se o tempo do leilão é de pelo menos 1 minuto
    if(diff.total_seconds() < 60):
        return "O horário de término do leilão deve ser pelo menos 1 minuto maior que o horario atual", 400 
    
    #Conexão com o redis
    redisCon = redis.StrictRedis(host='redis-manager', port=6379, db=0, decode_responses=True)
    lock = RedisLock(redisCon, 'lock')
    if(lock.acquire()):
        try:
            cod_leilao = redisCon.incr('contador_leiloes')
            leilao = {"titulo":titulo, "descricao":descricao, "precoinicial":precoInicial, "horariotermino": horarioTermino}
            #Insere o leilão no redis
            redisCon.hset(f'leilao-{cod_leilao}', mapping = leilao)
            leilaoComCodigo = leilao.copy()
            leilaoComCodigo['codigo'] = cod_leilao
            leilaoComCodigo['horariotermino'] = datetime.fromisoformat(leilaoComCodigo['horariotermino']).strftime("%d/%m/%Y %H:%M")
            redisPubSub.publish("novo_leilao", json.dumps(leilaoComCodigo))
            
            data = datetime.fromisoformat(leilao['horariotermino'])

            diffseconds = int((data - datetime.now()).total_seconds());

            #Insere os registros de expiração no redis que funcionam como contadores
            redisPubSub.setex(f'leilaoexpira-{cod_leilao}', diffseconds, 'on')
            redisPubSub.setex(f'leilaoavisoexpira-{cod_leilao}', diffseconds-30, 'on')

            return "Leilão criado"
        except:
            return "Ocorreu um erro ao cadastrar o leilão", 400
        finally:
            lock.release()

@app.route('/view-auctions')
def viewAuctions():
    print("Visualização de leilões na instância de ID: " + str(id_server))
    dadosLeiloes = []
    #Se conecta no redis
    redisCon = redis.StrictRedis(host='redis-worker', port=6379, db=0, decode_responses=True)

    try:
        #Pega as chaves de todos os leilões
        chaves_leiloes = redisCon.keys("leilao-*")

        for chave in chaves_leiloes:
            #Consulta o leilão
            dadosLeilao = redisCon.hgetall(chave)
            #Consulta o lance atual daquele leilão
            codleilao = chave.split('-')[1];
            dadosLance = redisCon.zrange(f'lance-{codleilao}', -1, -1, withscores=True)
            #Cria um objeto do leilão
            dadosLeilaoEspecifico = {
                "codigo": codleilao, 
                "titulo": dadosLeilao["titulo"],
                "descricao": dadosLeilao["descricao"],
                "horariotermino": datetime.fromisoformat(dadosLeilao["horariotermino"]).strftime("%d/%m/%Y %H:%M"),
                "titulo": dadosLeilao["titulo"],
                "precoinicial": dadosLeilao["precoinicial"],
                "cpflanceatual": dadosLance[0][0] if dadosLance else None,
                "valorlanceatual": dadosLance[0][1] if dadosLance else None,
                "ativo": "Não" if datetime.fromisoformat(dadosLeilao["horariotermino"]) < datetime.now() else "Sim"
            }
            #Coloca o objeto na lista
            dadosLeiloes.append(dadosLeilaoEspecifico)
        #Renderiza a tela de leilões passando os leilões
        return render_template('leiloes.html', leiloes=dadosLeiloes)
    except:
        return "Ocorreu um erro ao consultar os leilões", 400


@app.route('/place-bid', methods=['POST'])
def placeBid():
    print("Criação de lance na instância de ID: " + str(id_server))
    #Capturando os dados do lance
    dados = request.get_json()
    cpf = dados.get('cpf')
    valor = None
    #Verifica se o valor é um número
    try:
        valor = float(dados.get('valor'))
    except: 
        return "O valor do lance tem que ser um número", 400
    leilao = None
    #Verifica se o codigo do leilão é um número inteiro
    try:
        leilao = int(dados.get('leilao'))
    except: 
        return "O codigo do leilão tem que ser um número inteiro", 400

    #Conexão com o redis
    redisCon = redis.StrictRedis(host='redis-manager', port=6379, db=0, decode_responses=True)
    lock = RedisLock(redisCon, 'lock')
    if(lock.acquire()):
        try:
            #Verifica se o leilão existe
            if(redisCon.exists(f'leilao-{leilao}')):
                #Pega as informações do leilão
                leilaoRedis = redisCon.hgetall(f'leilao-{leilao}')
                #Verifica se ele já não expirou
                if(datetime.fromisoformat(leilaoRedis['horariotermino']) < datetime.now()):
                    return "Esse leilão ja expirou", 400
                
                maior = None;
                #Pega o maior valor de lance do leilão
                if(redisCon.exists(f'lance-{leilao}')):
                    #Se o leilão tem lance, pega o valor do maior lance
                    maior = redisCon.zrange(f'lance-{leilao}', -1, -1, withscores=True)[0][1]
                else:
                    #Se o leilão não tem lance, pega o preço inicial do leilão
                    maior = redisCon.hget(f'leilao-{leilao}', 'precoinicial');

                #Se o valor for maior que o maior valor de lance do leilão
                if(valor > float(maior)):
                    #Adicionando lance
                    redisCon.zadd(f'lance-{leilao}', {cpf: valor})
                    #Notifica que um lance foi criado, passando as informações do lance
                    redisPubSub.publish("novo_lance", json.dumps({"cpf": cpf, "valor":valor, "leilao": leilao}))

                    return "Lance realizado"
                else:
                    return f'O lance tem que ser no mínimo maior que {maior}', 400
            else:
                return "Leilão não existente", 400
        except:
            return "Ocorreu um erro ao cadastrar o lance", 400
        finally:
            lock.release()

@app.route('/auction/<int:auction_id>')
def auctionDetails(auction_id):
    print("Visualização de leilão na instância de ID: " + str(id_server))
    dadosLeilao = None;
    dadosLances = None;

    #Conexão com o redis
    redisCon = redis.StrictRedis(host='redis-worker', port=6379, db=0, decode_responses=True)
    
    try:
        #Verifica se o leilão existe
        if(redisCon.exists(f'leilao-{auction_id}')):
            #Pega as informações do leilão
            dadosLeilaoRedis = redisCon.hgetall(f'leilao-{auction_id}');
            
            #Pega as informações dos lances do leilão
            dadosLancesRedis = redisCon.zrange(f'lance-{auction_id}', 0, -1, withscores=True)
            
            #Cria um objeto com as informações do leilão
            dadosLeilao = {
                "titulo": dadosLeilaoRedis["titulo"],
                "descricao": dadosLeilaoRedis["descricao"],
                "horariotermino": datetime.fromisoformat(dadosLeilaoRedis["horariotermino"]).strftime("%d/%m/%Y %H:%M"),
                "precoinicial": dadosLeilaoRedis["precoinicial"],
                "precoatual": dadosLancesRedis[len(dadosLancesRedis)-1][1] if dadosLancesRedis else None,
                "leilao": auction_id,
                "ativo": "Não" if datetime.fromisoformat(dadosLeilaoRedis["horariotermino"]) < datetime.now() else "Sim"
            }

            dadosLances = [{"cpf": cpf, "valor":valor} for cpf, valor in dadosLancesRedis]

            #Renderiza a tela de leilão passando essas informações do leilão
            return render_template('leilao.html', leilao=dadosLeilao, lances=dadosLances)
        else:
            return "Leilão não existente", 400

    except:
        return "Ocorreu um erro ao consultar o leilão", 400
if __name__ == '__main__':
    socket.run(app, port=8000, host='0.0.0.0', allow_unsafe_werkzeug=True)
