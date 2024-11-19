import os
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
BROKER = os.environ.get('BROKER', 'default_broker_url')
USERNAME = os.environ.get('USERNAME', 'default_username')
PASSWORD = os.environ.get('PASSWORD', 'default_password')
PORT = 8883
TOPIC_COMMAND = "home/esp32/leds"
TOPIC_STATUS = "home/esp32/status"

# Cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(USERNAME, PASSWORD)
mqtt_client.tls_set()
mqtt_client.tls_insecure_set(False)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT!")
        client.subscribe(TOPIC_STATUS)
    else:
        print(f"Erro ao conectar: {rc}")

def on_message(client, userdata, msg):
    global led_status
    try:
        payload = json.loads(msg.payload.decode())
        for led, state in payload.items():
            if led in led_status:
                led_status[led] = state
        print(f"Estado atualizado dos LEDs: {led_status}")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_led', methods=['POST'])
def update_led():
    global led_status
    data = request.get_json()
    for led, state in data.items():
        if led in led_status:
            led_status[led] = state
    mqtt_payload = json.dumps(led_status)
    mqtt_client.publish(TOPIC_COMMAND, mqtt_payload)
    return jsonify({"status": "OK", "led_status": led_status}), 200

@app.route('/led_status', methods=['GET'])
def get_led_status():
    return jsonify(led_status)

if __name__ == '__main__':
    # Render exige que a aplicação Flask use a porta definida na variável de ambiente PORT
    port = int(os.environ.get('PORT', 5000))  # Usa a porta do ambiente ou 5000 por padrão
    app.run(host='0.0.0.0', port=port)
