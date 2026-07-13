import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from gtts import gTTS

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# Memória do Sistema super enxuta
sistema_db = {
    "historico": [], # Guarda os últimos 4 chamados
    "aviso": "Prefeitura Municipal: Mantenha seus cuidados com a saúde em dia e atualize seu cadastro."
}

def create_app():
    app = Flask(__name__)
    socketio.init_app(app)

    audios_dir = os.path.join(app.root_path, 'static', 'audios')
    os.makedirs(audios_dir, exist_ok=True)

    @app.route('/')
    def route_doctor():
        return render_template('doctor.html')

    @app.route('/tv')
    def route_tv():
        return render_template('tv.html')

    @app.route('/admin')
    def route_admin():
        return render_template('admin.html')

    # --- COMUNICAÇÃO (SOCKETS) ---
    
    @socketio.on('connect')
    def handle_connect():
        # Quando a TV ou Admin ligam, recebem o aviso e histórico atual
        emit('sync_inicial', sistema_db)

    # Admin: Atualiza o texto do letreiro rodapé
    @socketio.on('update_aviso')
    def handle_update_aviso(novo_aviso):
        sistema_db["aviso"] = novo_aviso
        emit('sync_aviso', novo_aviso, broadcast=True)

    # Médico: Dispara a chamada
    @socketio.on('emit_call')
    def handle_call(data):
        if not data.get('paciente'):
            return
        
        # Atualiza o Histórico (mantém apenas os últimos 4 chamados)
        chamada_simples = {"paciente": data['paciente'], "sala": data['sala']}
        sistema_db["historico"].insert(0, chamada_simples)
        if len(sistema_db["historico"]) > 4:
            sistema_db["historico"].pop()
        
        # Geração da Voz
        texto_fala = f"Atenção. Paciente: {data['paciente']}. Dirija-se ao {data['sala']}."
        tts = gTTS(text=texto_fala, lang='pt', tld='com.br')
        arquivo_voz = os.path.join(audios_dir, 'voz.mp3')
        tts.save(arquivo_voz)
        
        data['cache_buster'] = int(time.time())
        data['historico'] = sistema_db['historico'] # Envia a lista atualizada para as TVs
        
        emit('sync_tv', data, broadcast=True)

    return app