# Leilão Online Distribuido

## Integrantes do grupo
- Luis Felipi Cruz de Souza [@LuisFSouza](https://github.com/LuisFSouza)
- Ryan de Melo Andrade [@MasteryRyge](https://github.com/MasteryRyge)

## Descrição
O sistema consiste de uma plataforma de leilões online, onde os usuários podem criar leilões, visualizar leilões e fazer lances nos leilões.
Na tela inicial o usuário pode ver os leilões, incluindo as seguintes informações destes: titulo, descrição, valor inicial, o lance atual (tanto o CPF de quem fez quanto o valor), o horário de término e um status se ele está ativo ou não. Também, para cada leilão é disponibilizado um botão de fazer lance e outro para visualizar o leilão, onde você pode visualizar o leilão com mais detalhes, incluindo os lances feitos. Este botão de fazer lance é desativado quando o leilão ja expirou ou expira (este caso é detalhado abaixo).
O lance atual, o status se ele está ativo e os leilões em si são atualizados em tempo real. Então quando alguem faz um lance em um leilão, o lance atual desse leilão nesta tela é atualizado. Também, quando um leilão está proximo de expirar (30 segundos), o status do leilão mostra um aviso, e quando o leilão realmente expira, o status dele é colocado como não ativo, sendo o botão de fazer lance desativado. Por fim, também, quando um leilão é cadastrado por alguem ele é incluido nesta tela. 
O botão de fazer lance mostra um formulário onde o usuário pode cadastrar um lance, fornecendo seu CPF e o valor do lance e clicando no botão de cadastrar.
Com relação a realização de lances, se o leilão ainda não tem lances, o valor do lance tem que ser pelo menos maior que o valor minimo do leilão. Caso o leilão ja tenha um lance, o valor do lance tem que ser pelo menos maior que o maior lance do leilão.
Essa tela também apresenta um botão de cadastrar leilão, que mostra um formulário onde o usuário pode cadastrar um lance, fornecendo seu titulo, descrição, preço inicial e horário de término. Só é possivel cadastrar leilão com pelo menos 1 minuto de duração.

A tela de visualização de leilão mostra um leilão específico, incluindo as seguintes informações: titulo, descrição, valor inicial, o lance atual (tanto o CPF de quem fez quanto o valor), o horário de término, um status se ele está ativo ou não, e os lances realizados até o momento, mostrando o cpf e o valor de cada lance.
Assim como na outra tela, o lance atual e o status de ativo são atualizados em tempo real da mesma forma. Porém aqui os lances também são atualizados em tempo real, então quando um lance é feito neste leilão, ele é incluido nesta tela.


## Tecnologias utilizadas
<div >
	<table>
		<tr>
        <td><code><img width="50" src="https://user-images.githubusercontent.com/25181517/183423507-c056a6f9-1ba8-4312-a350-19bcbc5a8697.png" alt="Python" title="Python"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/flask.png" alt="Flask" title="Flask"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/redis.png" alt="Redis" title="Redis"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/html.png" alt="HTML" title="HTML"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/css.png" alt="CSS" title="CSS"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/javascript.png" alt="Javascript" title="Javascript"/></code></td>
        <td><code><img width="50" src="https://socket.io/images/logo.svg" alt="Socket.IO" title="Socket.IO"/></code></td>
        <td><code><img width="50" src="https://raw.githubusercontent.com/marwin1991/profile-technology-icons/refs/heads/main/icons/docker.png" alt="Docker" title="Docker"/></code></td>
		</tr>
	</table>
</div>

* O Backend da aplicação foi feito com python, utilizando o framework flask.
* O Frontend da aplicação foi feito utilizando HTML, CSS e Javascript. Para a comunicação com o servidor em tempo real, foi utilizado a biblioteca Socket.IO 
* Utilizamos multipass para criar os nós do nosso sistema distribuido, junto ao Docker e ao Docker Swarm para orquestrar e gerenciar os serviços, e também HAProxy para balancear carga. 

## Multipass + Docker

1. **VMs**: Criando as duas maquinas virtuais que serão os nós do nosso sistema distribuído, usando multipass 
```
multipass launch --name flask --cpus 1 --memory 1G --disk 5G
multipass launch --name redis --cpus 1 --memory 1G --disk 5G
```

2. **Instalação Docker e Docker Compose**: Em cada uma das máquinas virtuais, instale o Docker e o Docker Compose, e inicialize o Docker, você pode usar o comando `multipass shell nomevm` para acessar uma maquina virtual.
```
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo apt install docker-compose
```

3. **Configurações no nó manager**: Acesse o nó manager, que será o chamado flask, usando o comando: `multipass shell flask`.

	3.1. **Cluster Swarm**: Inicialize o cluster Swarm. 
	```
	sudo docker swarm init --advertise-addr 'ip do nó manager'
	```
	3.2. **Workers**: Acesse nosso nó worker, que será o chamado redis, usando `multipass shell redis`, entre no cluster swarm como worker (o comando do bloco anterior irá disponibilizar um comando que você deve executar no nó worker), e depois retorne para o nó manager usando `multipass shell flask`. 

	3.3. **Criando os arquivos**: Crie uma pasta chamada TRABALHOFINAL_SD e coloque dentro dela todos os arquivos que estão dentro da pasta TRABALHOFINAL_SD do repositório. Você pode usar o `multipass transfer` para facilitar esta etapa.

	3.4. **Antes de prosseguir, entre dentro da pasta TRABALHOFINAL_SD e se mantenha nela**.

	3.5. **Construindo a imagem e iniciando os containers**: Agora, construa a imagem Docker e inicie os containers usando o Docker Compose.
	```
	sudo docker-compose up -d
	```
	3.6. **Subindo a Stack**: Agora, faça o deploy da Stack no cluster Swarm usando o Docker Stack.
	```
	sudo docker stack deploy --compose-file compose.yml stackleilao
	```
	3.7. **Enviando as réplicas do redis para o nó work**: Por fim, garantimos que as réplicas do Redis rodem no nó worker (redis).
	```
	sudo docker service update --constraint-add "node.hostname==redis" stackleilao_redis-manager
	sudo docker service update --constraint-add "node.hostname==redis" stackleilao_redis-worker
	sudo docker service update --constraint-add "node.hostname==redis" stackleilao_redis-pub-sub
	```

4.  **Acessando a aplicação**: Acesse a aplicação usando o ip do nó manager: `ip-no-manager:80/view-auctions`

## Testes
Abaixo a descrição dos testes executados
<hr>

<strong>Teste</strong>: Criar lance sem passar alguma das informações.

<strong>Saida</strong>: Informação solicitada ao usuário

---------------------

<strong>Teste</strong>: Criar um leilão sem passar alguma das informações.

<strong>Saida</strong>: Informação solicitada ao usuário

---------------------

<strong>Teste</strong>: Criar lance com valor abaixo do maior lance do leilão (leilão sem lance).

<strong>Saida</strong>: Mensagem de aviso mostrada dizendo que o valor do lance tem que ser maior que o valor inicial do leilão (em valor)

---------------------

<strong>Teste</strong>: Criar lance com valor abaixo do maior lance do leilão (leilão com lance).

<strong>Saida</strong>: Mensagem de aviso mostrada dizendo que o valor do lance tem que ser maior que o valor do maior lance do leilão (em valor)

---------------------

<strong>Teste</strong>: Criar lance em um leilão expirado.

<strong>Saida</strong>: Mensagem de aviso mostrada dizendo que o leilão ja expirou.

---------------------

<strong>Teste</strong>: Criar leilão com menos de 1 minuto.

<strong>Saida</strong>: Mensagem de aviso mostrada informando que o leilão tem que ter pelo menos 1 minuto de duração

---------------------

<strong>Teste</strong>: Fazer lance no leilão que acabou de ser recebido via atualização, verificando se ele é feito corretamente e se ele é propagado em tempo real para as telas de visualização de leilões e de visualização de leilão.

<strong>Saida</strong>: Leilão feito corretamente, e ambas as telas de visualização de leilões e de visualização de leilão tiveram seus valores atualizados.

---------------------

<strong>Teste</strong>: Criar um leilão que irá expirar rápido, verificando as mudanças nas tags de ativo em tempo real nas telas de visualização de leilão e visualização de leilões.

<strong>Saida</strong>: Leilão criado corretamente, e ambas as telas de visualização de leilões e de visualização de leilão tiveram suas tags de ativo atualizados.

---------------------

<strong>Teste</strong>: Criando um leilão, verificando as mudanças em tempo real nas telas de leilões

<strong>Saida</strong>: Leilão criado corretamente, visualizações de leilão foram atualizadas com o novo leilão

---------------------

<strong>Teste</strong>: Tela de visualização de leilões

<strong>Saida</strong>: Mostrando leilões corretamente

---------------------

<strong>Teste</strong>: Tela de visualização de leilão

<strong>Saida</strong>: Mostrando o leilão corretamente

---------------------

<strong>Teste</strong>: Testando o balanceador de carga, mandando varias requisições

<strong>Saida</strong>: Requisições sendo distribuidas corretamente

---------------------

<strong>Teste</strong>: Criando lance normalmente.

<strong>Saida</strong>: Lance criado corretamente, e telas de visualização de leilões e de leilão atualizadas em tempo real.

---------------------

<strong>Teste</strong>: Criando leilão normalmente.

<strong>Saida</strong>: Leilão criado corretamente, e as visualização de leilões atualizadas em tempo real.

---------------------

<strong>Teste</strong>: Visualizar leilão inexistente.

<strong>Saida</strong>: Irá mostrar a mensagem de leilão inexistente

---------------------

<strong>Teste</strong>: Fazer lance em um leilão inexistente.

<strong>Saida</strong>: Irá mostrar a mensagem de leilão inexistente

---------------------

<strong>Teste</strong>: Testando o balanceador de carga, mandando varias requisições

<strong>Saida</strong>: Requisições sendo distribuidas corretamente

---------------------


### Execução do projeto localmente, sem docker
Para executar o projeto localmente, siga os seguintes passos:

1. **Clone o repositório**: Clone este repositório em sua máquina local utilizando o Git
```
git clone https://github.com/LuisFSouza/leilaodistribuido.git
```

2. **Instalações**: Instale o redis e o python, caso não tiver instalado

3. **Dependências**: Instale as dependências da aplicação.
```
pip install flask
pip install redis
pip install flask_socketio
pip install redis_lock
```

3. **Redis**: Inicialize o redis com o comando 
```
redis-server --notify-keyspace-events Ex
```

4.  **Aplicação**: Execute a aplicação
```
py app.py
```

5.  **Acesse a aplicação**: Acesse a aplicação na rota `http://127.0.0.1:8000/view-auctions`
