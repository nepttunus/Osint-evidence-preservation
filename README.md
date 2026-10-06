# Plataforma Modular de Captura e Preservação de Evidência Digital para OSINT

Plataforma modular para captura e preservação de evidência digital web em contexto OSINT.  
A solução combina uma **browser extension** para interação com o utilizador com um **motor local de captura e preservação**, responsável pela recolha de artefactos, geração de metadados, hashing, manifest, assinatura, cadeia de custódia e empacotamento final.

## Visão geral

O objetivo do projeto é permitir a recolha estruturada de evidência digital a partir do browser, preservando contexto técnico e mecanismos básicos de integridade e verificação posterior.

### Arquitetura

    [Browser]
       |
       v
    [Browser Extension]
       |
       v
    [Local API / Bridge]
       |
       v
    [Motor Local de Captura e Preservação]
       |
       +--> screenshot
       +--> HTML
       +--> PDF
       +--> metadados
       +--> manifest
       +--> assinatura
       +--> cadeia de custódia
       |
       v
    [Pacote ZIP / output]

## Funcionalidades principais

- Captura iniciada diretamente a partir do browser
- Obtenção do URL ativo no separador corrente
- Geração de screenshot, HTML, PDF, HAR e trace
- Recolha de metadados técnicos da execução
- Cálculo de hashes e criação de manifest
- Assinatura do manifest
- Registo de cadeia de custódia
- Geração de relatórios auxiliares
- Empacotamento final em ZIP
- Verificação posterior de integridade sobre pasta ou ZIP

## Pré-requisitos

- Python 3.9 ou superior
- Ambiente virtual Python
- Dependências em `requirements.txt`
- Playwright com Chromium instalado
- Google Chrome ou Microsoft Edge para a extensão

## Instalação

Criar e ativar ambiente virtual:

    python -m venv .venv
    source .venv/bin/activate

Instalar dependências:

    pip install -r requirements.txt
    python -m playwright install chromium

## Arranque do motor local

Executar a API local:

    uvicorn engine.api.app:app --host 127.0.0.1 --port 8000 --reload

Verificação rápida do serviço:

    curl http://127.0.0.1:8000/health

## Carregamento da browser extension

1. Abrir `chrome://extensions/` ou `edge://extensions/`
2. Ativar **Developer mode**
3. Selecionar **Load unpacked**
4. Escolher a pasta `extension/`

## Fluxo de utilização

1. Abrir uma página Web no browser
2. Abrir a browser extension
3. Confirmar o URL ativo apresentado no popup
4. Clicar em **Capturar evidência**
5. A extensão envia o pedido ao motor local
6. O motor local executa a captura e gera os artefactos
7. O popup apresenta a pasta de execução e o caminho do ZIP final

## Execução direta via CLI

Captura simples:

    python -m engine.src.main capture https://example.com

Captura com opções adicionais:

    python -m engine.src.main capture https://example.com --output-dir output --timeout-ms 30000 --actor cli_user

## Verificação de integridade

Verificar uma pasta de execução:

    python -m engine.src.main verify output/<nome_da_execucao>

Verificar o ZIP final:

    python -m engine.src.main verify output/<nome_da_execucao>/evidence_bundle.zip

## Testes

Executar a suite de testes:

    python -m pytest -q

## Estrutura do projeto

    .
    ├── engine/
    │   ├── api/
    │   │   └── app.py
    │   └── src/
    │       ├── capture.py
    │       ├── cli.py
    │       ├── custody.py
    │       ├── hashing.py
    │       ├── main.py
    │       ├── manifest.py
    │       ├── package.py
    │       ├── reporting.py
    │       ├── service.py
    │       ├── signature.py
    │       └── verify.py
    ├── extension/
    │   ├── manifest.json
    │   ├── popup.html
    │   └── popup.js
    ├── docs/
    ├── tests/
    └── output/

## Exemplo de output

Cada execução gera uma pasta estruturada semelhante a esta:

    output/example.com_YYYYMMDDTHHMMSSZ/
    ├── artifacts/
    │   ├── capture_metadata.json
    │   ├── console_logs.json
    │   ├── http_metadata.json
    │   ├── network.har
    │   ├── page.html
    │   ├── page.pdf
    │   ├── screenshot.png
    │   └── trace.zip
    ├── chain_of_custody.json
    ├── evidence_bundle.zip
    ├── keys/
    │   └── public_key.pem
    ├── manifest.json
    ├── manifest.sig
    ├── report.json
    └── report.md

## Estado atual

O projeto corresponde a um **MVP funcional** com:
- browser extension
- API local
- motor local de captura e preservação
- geração real de artefactos
- verificação de integridade

## Limitações atuais

- sem multiutilizador
- sem backend remoto
- sem timestamping qualificado externo
- sem gestão distribuída de casos
- cadeia de custódia simplificada face a cenários forenses formais

## Atualização final de validação

Na sequência do feedback do orientador, o projeto foi atualizado para melhorar o tratamento da chave privada.

A chave privada passou a ser mantida fora do pacote de evidência e deixou de ser incluída no ficheiro ZIP gerado. O pacote ZIP contém apenas a chave pública necessária para verificação posterior. Esta alteração melhora o modelo de integridade e autenticidade, porque a posse do pacote de evidência deixa de incluir o material privado utilizado para assinar o manifesto.

A suite de testes automáticos foi também reforçada com um teste de empacotamento que valida que o ficheiro `private_key.pem` é excluído do ZIP de evidência, enquanto o ficheiro `public_key.pem` permanece disponível para verificação.

Resultado final da validação:

15 passed

## Validação alargada para o artigo (outubro de 2026)

O resultado de 15 testes acima corresponde à validação original. A revisão para o artigo acrescenta uma correção que torna obrigatória a assinatura do manifesto e uma avaliação automatizada com páginas controladas e sites reais.

- A suite sem browser da versão corrigida passou 22 testes, incluindo dez novos casos de regressão.
- Foram executadas 87 tentativas de captura: nove cenários controlados e 20 URLs públicas, com três repetições.
- Foram produzidos 27 pacotes controlados e 44 pacotes de sites reais. Os cenários controlados satisfizeram todas as asserções em 24/27 execuções.
- As 142 verificações de diretoria/ZIP intactos passaram. As 852 verificações de entradas modificadas foram rejeitadas.
- O cenário de conteúdo inserido após três segundos falhou as verificações de conteúdo. Seis pacotes de sites reais preservaram respostas HTTP de acesso negado/erro. A integridade do pacote não demonstra completude da aquisição.

Os resultados completos, ambientes, limitações e comandos de reprodução encontram-se em [evaluation/journal-2026](evaluation/journal-2026/README.md). Os testes com browser dessa avaliação usam Playwright 1.63.0 no Ubuntu 26.04. Não se afirma uma nova execução da suite completa de 25 testes no mesmo ambiente.
