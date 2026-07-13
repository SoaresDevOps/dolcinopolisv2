import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Usando eventlet para latência zero no WebSocket
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)