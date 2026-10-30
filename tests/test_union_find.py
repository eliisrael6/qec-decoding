from union_find import UnionFind


def test_starts_separate():
    uf = UnionFind(4)
    assert [uf.find(i) for i in range(4)] == [0, 1, 2, 3]


def test_union_joins_clusters():
    uf = UnionFind(4)
    uf.union(0, 1)
    assert uf.find(0) == uf.find(1)
    assert uf.find(2) != uf.find(0)


def test_union_is_transitive():
    # 0 joins 1, 2 joins 3, then 1 joins 3, so 0 to 3 are all one cluster
    uf = UnionFind(6)
    uf.union(0, 1)
    uf.union(2, 3)
    uf.union(1, 3)
    assert len({uf.find(i) for i in range(4)}) == 1
    assert uf.find(4) != uf.find(0)


def test_union_returns_root():
    uf = UnionFind(3)
    root = uf.union(0, 1)
    assert root == uf.find(0) == uf.find(1)


def test_union_by_size():
    uf = UnionFind(5)
    uf.union(0, 1)
    uf.union(0, 2)          # cluster {0, 1, 2} has size 3
    big_root = uf.find(0)
    uf.union(3, 0)          # {3} is smaller, so its root goes under big_root
    assert uf.find(3) == big_root
    assert uf.size[big_root] == 4


def test_union_within_one_cluster_changes_nothing():
    uf = UnionFind(3)
    uf.union(0, 1)
    root = uf.find(0)
    assert uf.union(1, 0) == root
    assert uf.size[root] == 2


def test_path_compression():
    uf = UnionFind(4)
    uf.parent = [0, 0, 1, 2]    # a chain built by hand: 3 -> 2 -> 1 -> 0
    assert uf.find(3) == 0
    assert uf.parent == [0, 0, 0, 0]