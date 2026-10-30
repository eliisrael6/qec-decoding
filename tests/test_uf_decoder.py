import numpy as np

from uf_decoder import Clusters, grow, grow_one_round, incident_edges, repetition_graph


def test_repetition_graph_shape():
    # d = 5: checks 0 to 3, boundary node 4, edge i is data bit i
    n_nodes, edges, boundary = repetition_graph(5)
    assert n_nodes == 5
    assert boundary == 4
    assert edges == [(4, 0), (0, 1), (1, 2), (2, 3), (3, 4)]


def test_is_active():
    c = Clusters(5, defects=[1], boundary=4)
    assert c.is_active(1)            # a lone defect is odd, so it should grow
    assert not c.is_active(2)        # not a defect
    assert not c.is_active(4)        # the boundary never needs to grow


def test_merge_two_defects_makes_even_cluster():
    c = Clusters(5, defects=[1, 2], boundary=4)
    c.merge(1, 2)
    assert c.uf.find(1) == c.uf.find(2)
    assert not c.is_active(1)        # 1 + 1 defects = even, so it stops


def test_merge_with_boundary_stops_growth():
    c = Clusters(5, defects=[3], boundary=4)
    c.merge(3, 4)
    assert not c.is_active(3)        # touching the boundary stops growth


def test_merge_same_cluster_twice_is_safe():
    c = Clusters(5, defects=[1, 2], boundary=4)
    c.merge(1, 2)
    c.merge(2, 1)                    # already together, nothing should change
    assert not c.is_active(1)


def test_one_round_between_two_defects():
    n_nodes, edges, boundary = repetition_graph(5)
    c = Clusters(n_nodes, defects=[1, 2], boundary=boundary)
    inc = incident_edges(n_nodes, edges)
    support = [0] * len(edges)
    newly = grow_one_round(c, inc, support)
    # edge 2 joins checks 1 and 2, and both clusters grow into it
    assert newly == [2]
    assert support == [0, 1, 2, 1, 0]


def test_grow_neighbouring_defects():
    n_nodes, edges, boundary = repetition_graph(5)
    c, grown = grow(n_nodes, edges, boundary, defects=[1, 2])
    assert c.uf.find(1) == c.uf.find(2)
    assert grown == [False, False, True, False, False]


def test_grow_defect_next_to_boundary():
    n_nodes, edges, boundary = repetition_graph(5)
    c, grown = grow(n_nodes, edges, boundary, defects=[0])
    assert c.uf.find(0) == c.uf.find(boundary)
    assert grown[0]


def test_grow_no_defects():
    n_nodes, edges, boundary = repetition_graph(5)
    c, grown = grow(n_nodes, edges, boundary, defects=[])
    assert not any(grown)


def test_every_cluster_ends_neutral():
    # after growth, every cluster is even or touches the boundary
    rng = np.random.default_rng(0)
    for d in (3, 5, 7):
        n_nodes, edges, boundary = repetition_graph(d)
        for _ in range(200):
            error = rng.random(d) < 0.3
            syndrome = error[:-1] ^ error[1:]
            defects = [int(i) for i in np.flatnonzero(syndrome)]
            c, _ = grow(n_nodes, edges, boundary, defects)
            assert not any(c.is_active(v) for v in defects)