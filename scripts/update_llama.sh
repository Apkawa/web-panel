#!/bin/bash
set -euo pipefail

# Аргументы
TAG_NAME="${1:-}"

# Целевая директория
TARGET_DIR="/opt/llama"
# Имя бинарника, на который создаём ссылку
BINARY_NAME="llama-server"
# Ссылка в /usr/local/bin/
LINK_BIN_ROOT="/usr/local/bin/"
LINK_PATH="$LINK_BIN_ROOT/llama-server"

# Показ справки
if [ "$TAG_NAME" = "-h" ] || [ "$TAG_NAME" = "--help" ]; then
    echo "Использование: $0 [TAG_NAME]"
    echo ""
    echo "Без аргументов — обновляет до последней версии."
    echo "TAG_NAME — устанавливает конкретную версию (например 1.7.5) или откатывает,"
    echo "если версия уже загружена."
    exit 0
fi

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

# Из имени файла извлекаем базовое имя директории (обычно llama-<tag>)
EXTRACTED_DIR_NAME="llama-$TAG_NAME"
# Полный путь к директории версии
VERSION_DIR="$TARGET_DIR/$EXTRACTED_DIR_NAME"

# ========== Логика с TAG_NAME (конкретная версия) ==========
if [ -n "$TAG_NAME" ]; then
    # Проверяем, существует ли уже эта версия — откат без скачивания
    if [ -d "$VERSION_DIR" ] && [ -f "$VERSION_DIR/$BINARY_NAME" ]; then
        echo "Версия $EXTRACTED_DIR_NAME уже загружена, пропускаем скачивание."
    else
        # Запрашиваем конкретный релиз через API
        RELEASE_JSON=$(curl -fsSL "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/$TAG_NAME")
        if [ -z "$RELEASE_JSON" ]; then
            echo "Ошибка: релиз $TAG_NAME не найден."
            exit 1
        fi

    fi
# ========== Логика без TAG_NAME (последняя версия) ==========
else
    # Получаем информацию о последнем релизе через GitHub API
    echo "Получение информации о последнем релизе..."
    RELEASE_JSON=$(curl -fsSL https://api.github.com/repos/ggml-org/llama.cpp/releases/latest)
    if [ -z "$RELEASE_JSON" ]; then
        echo "Ошибка: не удалось получить данные о последнем релизе."
        exit 1
    fi

    TAG_NAME=$(echo "$RELEASE_JSON" | jq -r '.tag_name')
    if [ -z "$TAG_NAME" ] || [ "$TAG_NAME" = "null" ]; then
        echo "Ошибка: не удалось определить tag_name последнего релиза."
        exit 1
    fi
    EXTRACTED_DIR_NAME="llama-$TAG_NAME"
    # Полный путь к директории версии
    VERSION_DIR="$TARGET_DIR/$EXTRACTED_DIR_NAME"
    echo "Последний релиз: $TAG_NAME"
fi

# Проверяем, существует ли уже эта версия — откат без скачивания
if [ -d "$VERSION_DIR" ] && [ -f "$VERSION_DIR/$BINARY_NAME" ]; then
    echo "Версия $EXTRACTED_DIR_NAME уже загружена, пропускаем скачивание."
else
    # Ищем asset
    ASSET_URL=$(echo "$RELEASE_JSON" | jq -r '.assets[] | select(.name | contains("ubuntu-vulkan-x64.tar.gz")) | .browser_download_url' | head -n1)
    if [ -z "$ASSET_URL" ]; then
        echo "Ошибка: asset с ubuntu-vulkan-x64.tar.gz не найден в релизе $TAG_NAME."
        exit 1
    fi

    ASSET_NAME=$(basename "$ASSET_URL")

    # Создаём целевую директорию, если её нет
    if [ ! -d "$TARGET_DIR" ]; then
        echo "Создаём директорию $TARGET_DIR"
        sudo mkdir -p "$TARGET_DIR"
    fi

    # Скачиваем архив во временную папку
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    echo "Скачивание $ASSET_NAME ..."
    curl -fSL -O "$ASSET_URL"

    if [ ! -f "$ASSET_NAME" ]; then
        echo "Ошибка: не удалось скачать файл."
        exit 1
    fi

    # Распаковываем
    echo "Распаковка $ASSET_NAME ..."
    tar -xzf "$ASSET_NAME"

    # После распаковки проверяем, что появилось
    if [ -d "$EXTRACTED_DIR_NAME" ]; then
        echo "Архив содержит директорию $EXTRACTED_DIR_NAME"
        sudo mv "$EXTRACTED_DIR_NAME" "$TARGET_DIR/"
    else
        echo "Архив не содержит общей директории, создаём $EXTRACTED_DIR_NAME"
        sudo mkdir -p "$TARGET_DIR/$EXTRACTED_DIR_NAME"
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

echo "Готово. Версия llama.cpp ($TAG_NAME) установлена и доступна по команде $BINARY_NAME."

llama-server --version
