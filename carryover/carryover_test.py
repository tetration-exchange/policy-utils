import carryover


def test_underlap():
    intervals = [(1, 3), (2, 5)]
    result = carryover.merge_intervals(intervals)
    assert list(result) == [(1, 5)]


def test_overlap():
    intervals = [(2, 3), (1, 5)]
    result = carryover.merge_intervals(intervals)
    assert list(result) == [(1, 5)]


def test_equal():
    intervals = [(1, 5), (1, 5)]
    result = carryover.merge_intervals(intervals)
    assert list(result) == [(1, 5)]


def test_not_equal_joined():
    intervals = [(1, 5), (6, 10)]
    result = carryover.merge_intervals(intervals)
    assert list(result) == [(1, 10)]


def test_not_equal_disjoint():
    intervals = [(1, 5), (7, 10)]
    result = carryover.merge_intervals(intervals)
    assert list(result) == [(1, 5), (7, 10)]


def test_merge_underlap():
    a = [{"proto": 6, "port": [1, 3]}]
    b = [{"proto": 6, "port": [2, 5]}]

    result = carryover.merge_l4_params(a, b)
    assert result == [{"proto": 6, "port": (1, 5)}]


def test_merge_two_protos():
    a = [{"proto": 6, "port": [1, 3]}]
    b = [{"proto": 17, "port": [2, 5]}]

    result = carryover.merge_l4_params(a, b)
    assert result == [{"proto": 17, "port": (2, 5)}, {"proto": 6, "port": (1, 3)}]


def test_merge_no_port_protos():
    a = [{"proto": 1}]  # ICMP
    b = [{"proto": None}]  # ANY

    result = carryover.merge_l4_params(a, b)
    assert result == [{"proto": 1}, {"proto": None}]


def test_merge_workspaces_default():
    w0 = {
        "default_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (2, 5)
            }, {
                "proto": 6,
                "port": (1, 3)
            }]
        }],
        "absolute_policies": []
    }

    w1 = {
        "default_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (4, 7)
            }, {
                "proto": 6,
                "port": (2, 5)
            }]
        }],
        "absolute_policies": []
    }

    carryover.do_merge(w0, w1)
    assert w1["default_policies"][0]["l4_params"] == [{"proto": 17, "port": (2, 7)}, {"proto": 6, "port": (1, 5)}]


def test_merge_workspaces_absolute():
    w0 = {
        "absolute_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (2, 5)
            }, {
                "proto": 6,
                "port": (1, 3)
            }]
        }],
        "default_policies": []
    }

    w1 = {
        "absolute_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (4, 7)
            }, {
                "proto": 6,
                "port": (2, 5)
            }]
        }],
        "default_policies": []
    }

    carryover.do_merge(w0, w1)
    assert w1["absolute_policies"][0]["l4_params"] == [{"proto": 17, "port": (2, 7)}, {"proto": 6, "port": (1, 5)}]


def test_merge_workspaces():
    w0 = {
        "default_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (2, 5)
            }, {
                "proto": 6,
                "port": (1, 3)
            }]
        }],
        "absolute_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": None
            }, {
                "proto": 1
            }]
        }],
    }

    w1 = {
        "default_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "abc",
            "provider_filter_id": "123",
            "l4_params": [{
                "proto": 17,
                "port": (4, 7)
            }, {
                "proto": 6,
                "port": (2, 5)
            }]
        }],
        "absolute_policies": [{
            "action": "ALLOW",
            "consumer_filter_id": "efg",
            "provider_filter_id": "456",
            "l4_params": [{
                "proto": 6,
                "port": (100, 200)
            }]
        }]
    }

    carryover.do_merge(w0, w1)
    assert w1["default_policies"][0]["l4_params"] == [{"proto": 17, "port": (2, 7)}, {"proto": 6, "port": (1, 5)}]
    assert w1["absolute_policies"][0]["l4_params"] == [{"proto": 6, "port": (100, 200)}]
    assert w1["absolute_policies"][1]["l4_params"] == [{"proto": None}, {"proto": 1}]
