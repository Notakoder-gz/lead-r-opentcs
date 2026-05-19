# Инструкция по настройке роботов Yahboom MicroROS-Pi5 для OpenTCS

Данный документ содержит полное руководство по первичной настройке, проверке систем и настройке автозапуска роботов Yahboom MicroROS-Pi5 (Raspberry Pi 5 + ESP32) для работы с сервером OpenTCS.

---

## 1. Концепция сети и архитектуры

1. **Сервер (ваша машина):** Запускает ядро `OpenTCS` и контейнер `yahboom_opentcs_adapter`. Сервер общается с роботами по Wi-Fi, используя ROS 2 (DDS).
2. **Raspberry Pi 5 (на роботе):** Выполняет высокоуровневую логику (Nav2, Lidar) на базе ROS 2.
3. **ESP32 (на роботе):** Контроллер двигателей, работающий на Micro-ROS.

**Важно о FastDDS:** Само ядро OpenTCS не использует FastDDS (оно работает через HTTP API). Однако наш `yahboom_opentcs_adapter` написан на ROS 2 и использует FastDDS для связи с роботом.
По умолчанию ROS 2 рассылает Multicast (широковещательные) пакеты для поиска устройств в сети. Если роботов в сети Wi-Fi будет несколько, этот трафик **обрушит** ESP32, и робот "зависнет". Чтобы этого избежать, мы переводим ROS 2 в режим **Unicast** (строгая связь точка-точка).

---

## 2. Первичный запуск и проверка (на роботе)

Подключитесь к Raspberry Pi робота (через SSH или подключив монитор/клавиатуру).

### 2.1. Настройка Unicast профиля (Решение проблемы с ESP32)
1. Создайте файл `fastdds_profiles.xml` в домашней директории пользователя `pi` (например, `/home/pi/fastdds_profiles.xml`):
   ```xml
   <?xml version="1.0" encoding="UTF-8" ?>
   <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastrtps_profiles">
       <participant profile_name="unicast_profile" is_default_profile="true">
           <rtps>
               <useBuiltinTransports>false</useBuiltinTransports>
               <userTransports>
                   <transport_id>udp_transport</transport_id>
               </userTransports>
           </rtps>
       </participant>
       <transport_descriptors>
           <transport_descriptor>
               <transport_id>udp_transport</transport_id>
               <type>UDPv4</type>
           </transport_descriptor>
       </transport_descriptors>
   </profiles>
   ```

2. Откройте `~/.bashrc` на роботе и добавьте в конец файла следующие строки:
   ```bash
   # Подгружаем ROS 2
   source /opt/ros/humble/setup.bash # Замените humble на jazzy, если используете новую ОС
   # Подгружаем рабочее пространство Yahboom (зависит от того, куда вы скачали их пакеты)
   source ~/yahboom_ws/install/setup.bash

   # Настройки сети
   export ROS_DOMAIN_ID=20
   export FASTDDS_DEFAULT_PROFILES_FILE=/home/pi/fastdds_profiles.xml
   ```
3. Примените изменения: `source ~/.bashrc`

### 2.2. Ручная проверка систем
Перед настройкой автозапуска убедитесь, что робот полностью исправен:

1. **Запустите Micro-ROS Agent:**
   Откройте терминал на Raspberry Pi и запустите агента для связи с ESP32 (обычно через serial-порт `/dev/ttyUSB0` или `/dev/ttyAMA0`):
   ```bash
   ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6
   ```
   *Вы должны увидеть сообщения о том, что ESP32 успешно подключился (Session established).*

2. **Проверка Лидара и Базовых узлов (в новом окне терминала):**
   ```bash
   ros2 launch yahboom_bringup yahboom_bringup.launch.py
   ```

3. **Проверка телеметрии:**
   В третьем окне терминала введите:
   ```bash
   ros2 topic echo /odom
   ```
   Вы должны увидеть поток координат. Если вы вручную покатаете робота по полу, цифры `x` и `y` должны меняться.

---

## 3. Настройка Автозапуска (Systemd)

Чтобы робот автоматически запускал Micro-ROS агента, драйверы, и лидар при включении питания и сразу "стучался" в OpenTCS, мы создадим сервисы Linux.

### 3.1. Создание скрипта запуска
Создайте файл `/home/pi/start_robot.sh`:
```bash
#!/bin/bash
# 1. Загружаем окружение (ОБЯЗАТЕЛЬНО для systemd)
source /opt/ros/humble/setup.bash
source /home/pi/yahboom_ws/install/setup.bash

export ROS_DOMAIN_ID=20
export FASTDDS_DEFAULT_PROFILES_FILE=/home/pi/fastdds_profiles.xml

# 2. Запускаем Micro-ROS Agent в фоне
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 &
AGENT_PID=$!

# Даем ESP32 5 секунд на подключение
sleep 5

# 3. Запускаем основные узлы робота (Лидар, одометрию, моторы)
ros2 launch yahboom_bringup yahboom_bringup.launch.py &
BRINGUP_PID=$!

# 4. Запускаем навигацию Nav2 (Опционально, для выполнения маршрутов OpenTCS)
# ros2 launch yahboom_nav2 navigation.launch.py map:=/home/pi/maps/my_map.yaml &
# NAV_PID=$!

# Ждем завершения процессов
wait $AGENT_PID $BRINGUP_PID
```
Сделайте скрипт исполняемым:
```bash
chmod +x /home/pi/start_robot.sh
```

### 3.2. Создание сервиса Systemd
Создайте файл сервиса `/etc/systemd/system/yahboom_robot.service`:
```ini
[Unit]
Description=Yahboom ROS 2 Robot Startup
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
ExecStart=/bin/bash /home/pi/start_robot.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3.3. Включение и проверка сервиса
1. Перезагрузите конфигурацию systemd:
   ```bash
   sudo systemctl daemon-reload
   ```
2. Включите автозапуск при старте:
   ```bash
   sudo systemctl enable yahboom_robot.service
   ```
3. Запустите сервис сейчас:
   ```bash
   sudo systemctl start yahboom_robot.service
   ```
4. Посмотрите логи, чтобы убедиться, что всё работает:
   ```bash
   sudo journalctl -u yahboom_robot.service -f
   ```

Теперь, каждый раз при включении Raspberry Pi, робот автоматически будет подключаться к сети Wi-Fi, запускать ROS 2 с Unicast-профилем и транслировать топики. Сервер OpenTCS (в лице нашего адаптера) автоматически подхватит эти топики, если они находятся в одном `ROS_DOMAIN_ID`.
