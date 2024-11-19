from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Estado inicial dos LEDs
led_status = {
    "led1": False,
    "led2": False,
    "led3": False,
    "led4": False
}

# Configurações do broker MQTT
BROKER = "1ef481efbcb74c5cba041287bb4703c0.s1.eu.hivemq.cloud"  # Broker URL do HiveMQ
PORT = 8883  # Porta segura (TLS)
USERNAME = "apiespled"  # Substitua pelo usuário do HiveMQ Cloud
PASSWORD = "Apiespled123."  # Substitua pela senha do HiveMQ Cloud
TOPIC_COMMAND = "home/esp32/leds"  # Tópico para enviar comandos
TOPIC_STATUS = "home/esp32/status"  # Tópico para receber status

# Cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(USERNAME, PASSWORD)
mqtt_client.tls_set()  # Configura o TLS
mqtt_client.tls_insecure_set(False)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT!")
        client.subscribe(TOPIC_STATUS)  # Subscreve no tópico de status
    else:
        print(f"Erro ao conectar: {rc}")

def on_message(client, userdata, msg):
    global led_status
    try:
        # Atualiza o status dos LEDs com base na mensagem recebida
        payload = json.loads(msg.payload.decode())
        for led, state in payload.items():
            if led in led_status:
                led_status[led] = state
        print(f"Status dos LEDs atualizado via MQTT: {led_status}")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

# Configurando callbacks do cliente MQTT
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Conectando ao broker
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_led', methods=['POST'])
def update_led():
    global led_status
    data = request.get_json()  # Obtendo JSON

    # Atualiza o estado dos LEDs
    for led, state in data.items():
        if led in led_status:
            led_status[led] = state

    # Publica no tópico MQTT
    mqtt_payload = json.dumps(led_status)
    mqtt_client.publish(TOPIC_COMMAND, mqtt_payload)
    print(f"Comando enviado ao MQTT: {mqtt_payload}")

    return jsonify({"status": "OK", "led_status": led_status}), 200

@app.route('/led_status', methods=['GET'])
def get_led_status():
    return jsonify(led_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
