FROM eclipse-temurin:21-jre

WORKDIR /opt/opentcs

# 1. Утилиты
RUN apt-get update && apt-get install -y wget unzip dos2unix findutils && rm -rf /var/lib/apt/lists/*

# 2. Скачивание (Версия 7.2.1 Binary)
RUN wget -q https://github.com/openTCS/opentcs/releases/download/v7.2.1/opentcs-7.2.1-bin.zip -O /tmp/opentcs.zip

# 3. Распаковка и копирование
RUN mkdir -p /tmp/install && \
    unzip -q /tmp/opentcs.zip -d /tmp/install && \
    # Ищем папку, где лежит startKernel.sh
    KERNEL_ROOT=$(find /tmp/install -name "startKernel.sh" -exec dirname {} \; | head -n 1) && \
    # Копируем СОДЕРЖИМОЕ этой папки (включая папку lib!) в /opt/opentcs
    cp -r "$KERNEL_ROOT"/. . && \
    rm -rf /tmp/opentcs.zip /tmp/install

# 4. Проверка структуры (важно для логов сборки)
# Мы должны увидеть папку lib и файл startKernel.sh в одном списке
RUN ls -F

# 5. Лечим скрипты и права (теперь смотрим в корень)
RUN dos2unix *.sh && chmod +x *.sh

# 6. Переменные окружения
ENV JAVA_TOOL_OPTIONS="-Duser.language=en -Duser.country=US"

EXPOSE 1099 8080 55200

# 7. Запуск (так как файл в корне)
CMD ["/bin/bash", "./startKernel.sh"]
