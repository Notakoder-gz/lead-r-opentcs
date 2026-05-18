import zenoh
import requests
import yaml
import json
import time

# Путь внутри контейнера (теперь он будет скопирован прямо в образ)
CONFIG_PATH = "/app/fleet_config.yaml"

def get_points_map(url_base):
    try:
        plant_model_url = f"{url_base}/plantModel"
        print(f"🗺️ Запрашиваем карту модели по адресу: {plant_model_url}")

        response = requests.get(plant_model_url, timeout=2)

        # Проверяем, что сервер ответил "ОК" (200), а не 404
        if response.status_code != 200:
            print(f"❌ Ошибка сервера. Код: {response.status_code}")
            return {}

        plant_model = response.json()

        # В OpenTCS точки лежат внутри массива 'points' в plantModel
        points_data = plant_model.get('points', [])

        # Создаем словарь { 'ИмяТочки': {'x': 1000, 'y': 2000} }
        points_dict = {p['name']: p['position'] for p in points_data if 'position' in p}

        print(f"✅ Карта успешно загружена! Найдено точек: {len(points_dict)}")
        return points_dict

    except Exception as e:
        print(f"❌ Не удалось распарсить карту точек: {e}")
        return {}

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_opentcs_data(url):
    try:
        response = requests.get(url, timeout=1)
        return response.json()
    except Exception as e:
        print(f"❓ Ошибка связи с OpenTCS: {e}")
        return []

def main():
    config = load_config()
    fm_cfg = config['fleet_manager']

    # Инициализация Zenoh
    z_conf = zenoh.Config()
    session = zenoh.open(z_conf)

    fleet_name = config['rmf_fleet']['name']
    pub = session.declare_publisher(f"rmf/robot_state/{fleet_name}")

    print(f"🚀 Адаптер {fleet_name} запущен. Ждем данные от OpenTCS...")

    url_base = fm_cfg['opentcs_api_url'].rsplit('/', 1)[0] # Отрезаем /vehicles
    points_cache = get_points_map(url_base)

    while True:
        vehicles = get_opentcs_data(fm_cfg['opentcs_api_url'])

        for v in vehicles:
            tcs_name = v.get('name')
            if tcs_name in config['robots']:
                # 1. Пробуем взять точные координаты
                pos = v.get('precisePosition')

                # 2. Если их нет, пробуем взять координаты точки, на которой стоит робот
                if pos is None:
                    curr_point = v.get('currentPosition')
                    pos = points_cache.get(curr_point)

                # 3. Если и точки нет — значит робот "в тумане"
                if pos is None:
                    print(f"⚠️ {tcs_name} не на точке и не имеет точных координат")
                    continue

                # 4. Формируем и отправляем состояние
                state = {
                    "name": tcs_name,
                    "model": "yahboom_r2",
                    "location": {
                        "x": pos.get('x', 0) / 1000.0, # мм -> м
                        "y": pos.get('y', 0) / 1000.0,
                        "yaw": 0.0,
                        "level_name": "L1"
                    },
                    "battery": v.get('energyLevel', 100),
                    "status": v.get('state', 'IDLE'),
                    "charger": config['robots'][tcs_name].get('charger')
                }

                pub.put(json.dumps(state))
                print(f"📡 [{tcs_name}] X: {state['location']['x']:.2f} Y: {state['location']['y']:.2f} Bat: {state['battery']}%")

        time.sleep(0.5)

if __name__ == "__main__":
    main()