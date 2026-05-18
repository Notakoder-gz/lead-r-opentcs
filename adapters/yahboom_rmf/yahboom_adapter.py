import sys
import json
import rclpy
import zenoh

import yaml
import os
import rmf_adapter as adpt
import rmf_adapter.vehicletraits as traits
import rmf_adapter.geometry as geometry
import rmf_adapter.graph as graph
import rmf_adapter.plan as plan

# 1. Класс-обработчик команд от Планировщика RMF (Наш задел на Этап 3)
class YahboomCommandHandle(adpt.RobotCommandHandle):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def clear(self):
        pass

    def stop(self):
        print(f"?? [{self.name}] Дашборд нажал СТОП!")

    def follow_new_path(self, waypoints, next_arrival_estimator, path_finished_callback):
        print(f"?? [{self.name}] Получен новый маршрут от RMF! Точек: {len(waypoints)}")
        # Здесь мы позже будем перехватывать маршрут и кидать его в OpenTCS

    def dock(self, dock_name, docking_finished_callback):
        print(f"?? [{self.name}] Команда на зарядку: {dock_name}")

def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"?? ВНИМАНИЕ: Файл конфигурации {config_path} не найден! Используются параметры по умолчанию.")
        return None
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # Загружаем конфигурацию роботов
    config_path = os.environ.get('ROBOTS_CONFIG_PATH', '/app/robots_config.yaml')
    config = load_config(config_path)

    # Передаем системные аргументы в ROS 2 (это важно для правильной инициализации)
    rclpy.init(args=sys.argv)
    adpt.init_rclcpp()
    print("Инициализация Yahboom Fleet Adapter...")

    # 2. Создаем ноду адаптера
    adapter = adpt.Adapter.make('yahboom_fleet_adapter')

    # Защита от тайм-аута
    if adapter is None:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Планировщик RMF (rmf_traffic_schedule) не найден!")
        print("   Адаптер ждал 60 секунд, но ядро RMF не ответило.")
        print("   Убедись, что контейнер с ядром запущен и ROS_DOMAIN_ID совпадает.")
        sys.exit(1)

    # Настраиваем параметры из конфига или дефолтные
    fleet_name = config.get('fleet_name', 'yahboom_fleet') if config else 'yahboom_fleet'

    if config and 'profile' in config:
        footprint_radius = config['profile'].get('footprint', 0.3)
        v_max = config['profile']['linear_limits'].get('v_max', 1.0)
        a_max = config['profile']['linear_limits'].get('a_max', 2.0)
        w_max = config['profile']['angular_limits'].get('w_max', 0.6)
        alpha_max = config['profile']['angular_limits'].get('alpha_max', 1.5)
    else:
        footprint_radius = 0.3
        v_max, a_max = 1.0, 2.0
        w_max, alpha_max = 0.6, 1.5

    # 3. Физика робота (меняем под реальные габариты Yahboom)
    profile = traits.Profile(geometry.make_final_convex_circle(footprint_radius))
    robot_traits = traits.VehicleTraits(
        linear=traits.Limits(v_max, a_max),
        angular=traits.Limits(w_max, alpha_max),
        profile=profile
    )

    # 4. Загружаем дорожный граф
    # ВАЖНО: Мы будем монтировать граф из deploy_maps
    nav_graph_path = "/app/0.yaml"
    try:
        nav_graph = graph.parse_graph(nav_graph_path, robot_traits)
        print(f"✅ Граф загружен. Точек: {nav_graph.num_waypoints}")
    except Exception as e:
        print(f"❌ Ошибка загрузки графа: {e}")
        sys.exit(1)

    # 5. Регистрируем флот в ядре RMF
    print(f"?? Регистрация флота {fleet_name}...")
    fleet = adapter.add_fleet(fleet_name, robot_traits, nav_graph)
    fleet.accept_task_requests(lambda req: True) # Разрешаем Дашборду кидать задачи

    # 6. Подключаем роботов к флоту
    update_handles = {}

    robots = config.get('robots', {'yahboom_01': {'start_waypoint': 0, 'start_yaw': 0.0}}) if config else {'yahboom_01': {'start_waypoint': 0, 'start_yaw': 0.0}, 'yahboom_02': {'start_waypoint': 0, 'start_yaw': 0.0}}

    for robot_name, robot_info in robots.items():
        start_wp = robot_info.get('start_waypoint', 0)
        start_yaw = robot_info.get('start_yaw', 0.0)
        starts = [plan.Start(adapter.now(), start_wp, start_yaw)]

        def create_callback(name):
            def cb(handle):
                update_handles[name] = handle
                print(f"🤖 [{name}] Успешно зарегистрирован в ядре RMF!")
            return cb

        cmd = YahboomCommandHandle(robot_name)
        fleet.add_robot(cmd, robot_name, profile, starts, create_callback(robot_name))
        print(f"Инициализация робота {robot_name} с wp={start_wp}, yaw={start_yaw}")

    # 7. Слушаем OpenTCS через Zenoh
    print("?? Подключение к Zenoh...")
    z_conf = zenoh.Config()
    session = zenoh.open(z_conf)

    def get_nearest_waypoint(x, y):
        nearest_idx = 0
        min_dist = float('inf')
        for i in range(nav_graph.num_waypoints):
            wp = nav_graph.get_waypoint(i)
            wp_loc = wp.location # Получаем [x, y] точки из графа
            dist = ((wp_loc[0] - x)**2 + (wp_loc[1] - y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        return nearest_idx

    def zenoh_callback(sample):
        try:
            data = json.loads(bytes(sample.payload).decode('utf-8'))
            name = data['name']

            if name in update_handles:
                loc = data['location']
                x = float(loc['x'])
                y = float(loc['y'])
                yaw = float(loc['yaw'])

                # 1. Находим ближайшую точку на графе
                wp_idx = get_nearest_waypoint(x, y)

                # 2. Создаем объект Start
                new_start = plan.Start(adapter.now(), wp_idx, yaw)

                # 3. Передаем СПИСОК (List[plan.Start])
                update_handles[name].update_position([new_start])

        except Exception as e:
            print(f"❌ Ошибка обработки Zenoh: {e}")

    sub_topic = f'rmf/robot_state/{fleet_name}'
    sub = session.declare_subscriber(sub_topic, zenoh_callback)
    print(f"?? Подписка Zenoh на {sub_topic} оформлена")

    # 8. Запускаем "мозг" адаптера
    print("📡 Адаптер запущен и готов к работе!")

    # Start the RMF adapter thread
    adapter.start()

    try:
        # The internal C++ RMF adapter spins in its own background threads.
        # We simply need to keep the Python main thread alive without using rclpy.spin()
        # on the internal C++ node object to prevent 'executor' attribute errors.
        import time
        while rclpy.ok():
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Остановка адаптера...")
    finally:
        session.close()
        rclpy.shutdown()

if __name__ == '__main__':
    main()