#!/bin/bash
set -euo pipefail

# Целевая директория
TARGET_DIR="/opt/llama"
# Имя бинарника, на который создаём ссылку
BINARY_NAME="llama-server"
# Ссылка в /usr/local/bin/
LINK_BIN_ROOT="/usr/local/bin/"
LINK_PATH="$LINK_BIN_ROOT/llama-server"

# Функция для проверки наличия команды
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Ошибка: $1 не установлен. Установите его и повторите."
        exit 1
    fi
}

# Проверяем необходимые команды
check_command curl
check_command jq
check_command tar
check_command sudo

# Получаем информацию о последнем релизе через GitHub API
echo "Получение информации о последнем релизе..."
LATEST_RELEASE_JSON=$(curl -s https://api.github.com/repos/ggml-org/llama.cpp/releases/latest)
if [ -z "$LATEST_RELEASE_JSON" ]; then
    echo "Ошибка: не удалось получить данные о последнем релизе."
    exit 1
fi

TAG_NAME=$(echo "$LATEST_RELEASE_JSON" | jq -r '.tag_name')
if [ -z "$TAG_NAME" ] || [ "$TAG_NAME" = "null" ]; then
    echo "Ошибка: не удалось определить tag_name последнего релиза."
    exit 1
fi
echo "Последний релиз: $TAG_NAME"

# Ищем asset с нужным файлом
ASSET_URL=$(echo "$LATEST_RELEASE_JSON" | jq -r '.assets[] | select(.name | contains("ubuntu-vulkan-x64.tar.gz")) | .browser_download_url' | head -n1)
if [ -z "$ASSET_URL" ]; then
    echo "Ошибка: не найден asset с ubuntu-vulkan-x64.tar.gz в последнем релизе."
    exit 1
fi

ASSET_NAME=$(basename "$ASSET_URL")
echo "Найден asset: $ASSET_NAME"

# Из имени файла извлекаем базовое имя директории (обычно llama-<tag>)
EXTRACTED_DIR_NAME="llama-$TAG_NAME"
# Полный путь к директории версии
VERSION_DIR="$TARGET_DIR/$EXTRACTED_DIR_NAME"

# Проверяем, существует ли уже эта версия
if [ -d "$VERSION_DIR" ]; then
    echo "Версия $EXTRACTED_DIR_NAME уже существует в $TARGET_DIR, пропускаем скачивание."
else
    # Создаём целевую директорию, если её нет
    if [ ! -d "$TARGET_DIR" ]; then
        echo "Создаём директорию $TARGET_DIR"
        sudo mkdir -p "$TARGET_DIR"
    fi

    # Скачиваем архив во временную папку
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    echo "Скачивание $ASSET_NAME ..."
    curl -L -O "$ASSET_URL"

    # Проверяем, что файл скачан
    if [ ! -f "$ASSET_NAME" ]; then
        echo "Ошибка: не удалось скачать файл."
        exit 1
    fi

    # Распаковываем
    echo "Распаковка $ASSET_NAME ..."
    tar -xzf "$ASSET_NAME"

    # После распаковки проверяем, что появилось
    # Архив может содержать либо сразу файлы, либо папку с именем версии.
    if [ -d "$EXTRACTED_DIR_NAME" ]; then
        # Уже есть папка с правильным именем
        echo "Архив содержит директорию $EXTRACTED_DIR_NAME"
        # Перемещаем её в TARGET_DIR
        sudo mv "$EXTRACTED_DIR_NAME" "$TARGET_DIR/"
    else
        # Предполагаем, что распаковались файлы в текущей директории (кроме архива)
        echo "Архив не содержит общей директории, создаём $EXTRACTED_DIR_NAME и перемещаем файлы"
        sudo mkdir -p "$TARGET_DIR/$EXTRACTED_DIR_NAME"
        # Перемещаем все файлы, кроме архива, в папку версии
        find . -maxdepth 1 -not -name "$ASSET_NAME" -not -name "." -exec sudo mv {} "$TARGET_DIR/$EXTRACTED_DIR_NAME/" \;
    fi

    # Очищаем временную папку
    cd /tmp/
    rm -rf "$TMP_DIR"
    echo "Распаковка завершена."
fi

# Проверяем, что бинарник существует в новой версии
if [ ! -f "$VERSION_DIR/$BINARY_NAME" ]; then
    echo "Ошибка: в распакованной версии не найден файл $BINARY_NAME."
    exit 1
fi

# Создаём символическую ссылку в /usr/local/bin/
echo "Обновление символической ссылки $LINK_PATH -> $VERSION_DIR/$BINARY_NAME"
sudo ln -sf "$VERSION_DIR/$BINARY_NAME" "$LINK_PATH"
sudo ln -sf "$VERSION_DIR/llama-bench" "$LINK_BIN_ROOT"
sudo ln -sf "$VERSION_DIR/llama-batched-bench" "$LINK_BIN_ROOT"
sudo ln -sf "$VERSION_DIR/llama-cli" "$LINK_BIN_ROOT"
sudo ln -sf "$VERSION_DIR/llama-fit-params" "$LINK_BIN_ROOT"
sudo ln -sf "$VERSION_DIR/llama-perplexity" "$LINK_BIN_ROOT"

echo "Готово. Последняя версия llama.cpp ($TAG_NAME) установлена и доступна по команде $BINARY_NAME."

llama-server --version
