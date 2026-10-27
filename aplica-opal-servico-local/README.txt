APLICA OPAL — SERVIÇO LOCAL
============================

REQUISITOS
- Python 3.10 ou superior
- Computador ligado à rede onde estão os dispositivos
- Autorização para verificar a rede e os equipamentos

WINDOWS
1. Extrai a pasta aplica-opal-servico-local.
2. Faz duplo clique em start.bat.
3. Se o Windows perguntar sobre a firewall, não abras o serviço à rede pública.
4. Abre http://127.0.0.1:8765 no navegador.
5. Mantém a janela do terminal aberta enquanto usas o painel.

macOS / Linux
1. Abre um terminal nesta pasta.
2. Executa: chmod +x start.sh
3. Executa: ./start.sh
4. Abre http://127.0.0.1:8765.

O QUE FAZ
- Serve o painel HTML localmente.
- Verifica o intervalo permitido 192.168.0.1–192.168.1.254.
- Consulta portas TCP comuns de gestão/vídeo (80, 443, 554, 8000, 8080, 8899).
- Mostra endereços que responderam e as portas encontradas.

LIMITAÇÕES IMPORTANTES
- Uma porta aberta não prova que o dispositivo é uma câmara.
- Esta versão não autentica em câmaras, não mostra vídeo e não envia comandos PTZ.
- Não inclui descoberta ONVIF por multicast.
- O serviço escuta apenas em 127.0.0.1 e não fica exposto a outros computadores.
- O intervalo de IPs só será alcançável se o computador tiver rota/rede configurada para ele.
- A pesquisa pode não encontrar dispositivos que bloqueiem essas portas ou usem portas diferentes.

SEGURANÇA
Usa apenas em redes e dispositivos que tens autorização para administrar.
Não coloques palavras-passe de câmaras no código ou em páginas públicas.
