import ipaddress


def wildcard_to_mask(ip_str: str) -> str:
    """
    >>> wildcard_to_mask("192.168.2.100")
    "192.168.2.100"
    >>> wildcard_to_mask("192.168.2.*")
    "192.168.2.0/24"
    >>> wildcard_to_mask("192.168.*.*")
    "192.168.0.0/16"
    >>> wildcard_to_mask("192.*.*.*")
    "192.0.0.0/8"
    """
    if "*" in ip_str:
        # Например, "192.168.2.*" превратится в "192.168.2.0/24"
        ip_str = ip_str.replace("*", "0") + "/24"
    return ip_str


def rule_to_networks(ips: list[str]) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []
    for rule in ips:
        try:
            # Если в правиле есть звездочка, заменяем её на нули и слэш для библиотеки
            if "*" in rule:
                # Например, "192.168.2.*" превратится в "192.168.2.0/24"
                rule = rule.replace("*", "0") + "/24"

            # Создаем объект сети (или одиночного IP)
            network = ipaddress.ip_network(rule, strict=False)
            networks.append(network)
        except ValueError:
            continue  # Пропускаем ошибочные записи в списке правил
    return networks


def is_ip_allowed(ip_str: str, allowed_ips: list[str]):
    # Превращаем строку IP пользователя в специальный объект для сравнения
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False  # Некорректный IP-адрес

    # Список разрешенных сетей и одиночных IP
    # Сюда можно писать: точные IP, подсети со слэшем и маски со звездочкой

    for network in rule_to_networks(allowed_ips):
        if ip in network:
            return True
    return False
