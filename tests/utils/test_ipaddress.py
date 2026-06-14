from ipaddress import IPv4Network

from web_panel.utils.ipaddress import is_ip_allowed, rule_to_networks, wildcard_to_mask


class TestWildcardToMask:
    def test_single_ip(self):
        assert wildcard_to_mask("192.168.2.100") == "192.168.2.100"

    def test_one_wildcard(self):
        assert wildcard_to_mask("192.168.2.*") == "192.168.2.0/24"

    def test_two_wildcards(self):
        assert wildcard_to_mask("192.168.*.*") == "192.168.0.0/16"

    def test_three_wildcards(self):
        assert wildcard_to_mask("10.*.*.*") == "10.0.0.0/8"
        assert wildcard_to_mask("192.*.*.*") == "192.0.0.0/8"

    def test_four_wildcards(self):
        assert wildcard_to_mask("*.*.*.*") == "0.0.0.0/0"

    def test_wildcard_not_at_end(self):
        # Звёздочка внутри сегмента — допустимая входная строка
        result = wildcard_to_mask("192.*.2.*")
        assert result == "192.0.2.0/16"

    def test_already_cidr(self):
        assert wildcard_to_mask("10.0.0.0/8") == "10.0.0.0/8"


class TestRuleToNetworks:
    def test_single_ip(self):
        networks = rule_to_networks(["192.168.1.1"])
        assert len(networks) == 1
        assert networks[0] == IPv4Network("192.168.1.1/32")

    def test_wildcard(self):
        networks = rule_to_networks(["192.168.2.*"])
        assert len(networks) == 1
        assert networks[0] == IPv4Network("192.168.2.0/24")

    def test_cidr(self):
        networks = rule_to_networks(["10.0.0.0/8"])
        assert len(networks) == 1
        assert networks[0] == IPv4Network("10.0.0.0/8")

    def test_multiple_rules(self):
        networks = rule_to_networks(["192.168.1.*", "10.0.0.0/8"])
        assert len(networks) == 2

    def test_skips_invalid(self):
        networks = rule_to_networks(["not-an-ip", "192.168.1.1"])
        assert len(networks) == 1
        assert networks[0] == IPv4Network("192.168.1.1/32")

    def test_empty_list(self):
        assert rule_to_networks([]) == []

    def test_all_invalid(self):
        assert rule_to_networks(["invalid", "broken"]) == []


class TestIsIpAllowed:
    def test_exact_match(self):
        assert is_ip_allowed("192.168.1.1", ["192.168.1.1"])

    def test_match_cidr(self):
        assert is_ip_allowed("10.0.0.50", ["10.0.0.0/8"])

    def test_match_wildcard(self):
        assert is_ip_allowed("192.168.2.100", ["192.168.2.*"])

    def test_no_match(self):
        assert not is_ip_allowed("172.16.0.1", ["192.168.1.*"])

    def test_multiple_rules_any_match(self):
        assert is_ip_allowed("10.0.0.1", ["192.168.1.*", "10.0.0.0/8"])

    def test_multiple_rules_no_match(self):
        assert not is_ip_allowed("172.16.0.1", ["192.168.1.*", "10.0.0.0/8"])

    def test_empty_rules(self):
        assert not is_ip_allowed("192.168.1.1", [])

    def test_invalid_ip(self):
        assert not is_ip_allowed("not-an-ip", ["192.168.1.*"])

    def test_invalid_rule_in_list(self):
        assert is_ip_allowed("192.168.1.1", ["bad-rule", "192.168.1.*"])

    def test_single_wildcard_subnet(self):
        assert is_ip_allowed("192.168.2.255", ["192.168.2.*"])
        assert not is_ip_allowed("192.168.3.1", ["192.168.2.*"])

    def test_dual_wildcard_subnet(self):
        assert is_ip_allowed("10.5.3.2", ["10.*.*.*"])
        assert not is_ip_allowed("11.0.0.1", ["10.*.*.*"])

    def test_zero_wildcard(self):
        assert is_ip_allowed("0.0.0.0", ["0.0.0.0/0"])
