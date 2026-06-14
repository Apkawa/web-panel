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
        parts = ip_str.split(".")
        wildcard_parts = sum(1 for p in parts if p == "*")
        prefix_length = 32 - (wildcard_parts * 8)
        ip_str = ip_str.replace("*", "0") + f"/{prefix_length}"
    return ip_str


def rule_to_networks(ips: list[str]) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []
    for rule in ips:
        try:
            rule = wildcard_to_mask(rule)
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
