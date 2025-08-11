Envio Automático de Mensagens via WhatsApp
Este projeto é uma aplicação desktop desenvolvida em Python com PyQt5 para envio automático de mensagens via WhatsApp, utilizando a biblioteca pywhatkit. 
O objetivo é facilitar o envio em massa de mensagens personalizadas para uma lista de contatos, otimizando processos de comunicação para negócios, 
equipes de vendas, eventos ou campanhas de marketing.

Funcionalidades:
Carregamento de contatos via arquivo CSV: permite importar contatos com os campos Nome e Telefone.
Lista visual dos contatos importados: para visualização e remoção de contatos antes do envio.
Envio de mensagens personalizadas: possibilidade de adicionar o nome do destinatário no início da mensagem.
Barra de progresso: acompanha o andamento do envio das mensagens.
Registro (log) detalhado: gera um arquivo de log com data/hora de envio, status por contato e erros.
Interface moderna e responsiva: botões com animações e layout amigável em tons pastéis.
Visualização do log: permite consultar o histórico de envios dentro da própria aplicação.

Tecnologias Utilizadas:
Python 3.x
PyQt5 (interface gráfica)
pandas (manipulação de dados CSV)
pywhatkit (envio de mensagens pelo WhatsApp via web)
threading com QThread para execução assíncrona do envio e manter a interface responsiva.
