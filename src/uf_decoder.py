"""
Union find decoder, part 1: growing clusters.

The decoding graph has one node per check, plus a boundary node. Each edge
is a place an error can happen. For the repetition code, edge i is data
bit i. A defect is a check that fired.

Growth works in rounds. Every active cluster (odd number of defects and
not touching the boundary) grows each of its edges by half. An edge that
reaches full growth joins the clusters at its two ends. Growth stops once
no cluster is active.
"""

from union_find import UnionFind


def repetition_graph(d):
    # checks are nodes 0 to d - 2, and node d - 1 is the boundary
    boundary = d - 1
    edges = [(boundary, 0)]                 # bit 0: boundary to check 0
    for i in range(1, d - 1):
        edges.append((i - 1, i))            # bit i: check i - 1 to check i
    edges.append((d - 2, boundary))         # last bit: last check to boundary
    return d, edges, boundary


def incident_edges(n_nodes, edges):
    # for each node, the list of edges that touch it
    inc = [[] for _ in range(n_nodes)]
    for e, (u, v) in enumerate(edges):
        inc[u].append(e)
        inc[v].append(e)
    return inc


class Clusters:
    def __init__(self, n_nodes, defects, boundary):
        self.uf = UnionFind(n_nodes)
        # parity and touches_boundary are only kept up to date at roots
        self.parity = [0] * n_nodes
        self.touches_boundary = [False] * n_nodes
        for v in defects:
            self.parity[v] = 1
        self.touches_boundary[boundary] = True

    def is_active(self, v):
        """
        Return True if the cluster containing v still needs to grow.

        Find v's root. The cluster is active if the root's parity is 1 and
        the root does not touch the boundary.
        """
        root = self.uf.find(v)
        return self.parity[root] == 1 and not self.touches_boundary[root]

    def merge(self, u, v):
        """
        Join the clusters containing u and v.

        1. Find both roots. If they are the same, return straight away.
        2. Union the two roots and keep the root that union returns.
        3. Store the new parity at that root: the XOR (^) of the two old
           parities, since two odd clusters make an even one.
        4. Store touches_boundary at that root: True if either old root
           touched the boundary (use or).
        """
        # find roots of both clusters
        root_u = self.uf.find(u)
        root_v = self.uf.find(v)

        # stop if they are already in the same cluster
        if root_u == root_v:
            return

        # join the clusters
        root = self.uf.union(root_u, root_v)

        # update parity and boundary information
        self.parity[root] = self.parity[root_u] ^ self.parity[root_v]
        self.touches_boundary[root] = self.touches_boundary[root_u] or self.touches_boundary[root_v]


def grow_one_round(clusters, inc, support):
    """
    Grow every active cluster by half an edge, and return the list of
    edges that became fully grown this round.

    support[e] counts the halves of edge e grown so far: 0, 1 or 2.

    1. Make an empty set called to_grow.
    2. Loop over every node v (there are len(inc) of them). If v's cluster
       is active, get its root, then loop over v's edges in inc[v]. For each
       edge e that is not fully grown, add the pair (root, e) to to_grow.
       Using a set means a cluster grows each edge once per round, even if
       several of its nodes touch that edge.
    3. Make an empty list called newly_grown. Loop over each (root, e) in
       to_grow. If edge e is still under 2, add 1 to support[e], and if it
       has just reached 2, append e to newly_grown.
    4. Return newly_grown.
    """
    to_grow = set()

    for v in range(len(inc)):
        if clusters.is_active(v):
            root = clusters.uf.find(v)

            # add edges that haven't fully grown
            for e in inc[v]:
                if support[e] < 2:
                    to_grow.add((root, e))

    # grow the selected edges
    newly_grown = []

    for root, e in to_grow:
        if support[e] < 2:
            support[e] += 1

            # record edges that have finished growing
            if support[e] == 2:
                newly_grown.append(e)

    return newly_grown


def grow(n_nodes, edges, boundary, defects):
    # keep growing until every cluster is even or touches the boundary
    clusters = Clusters(n_nodes, defects, boundary)
    inc = incident_edges(n_nodes, edges)
    support = [0] * len(edges)
    while any(clusters.is_active(v) for v in defects):
        for e in grow_one_round(clusters, inc, support):
            u, v = edges[e]
            clusters.merge(u, v)
    grown = [s == 2 for s in support]
    return clusters, grown