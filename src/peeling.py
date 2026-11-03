"""
Union find decoder, part 2: peeling.

After growth, each cluster is a connected set of grown edges. Peeling
turns that into a correction. Build a tree inside each cluster, then work
in from the leaves. A leaf has only one tree edge, so if the leaf is a
defect, that edge must be in the correction.
"""

from collections import deque

import numpy as np

from uf_decoder import grow, repetition_graph


def spanning_forest(n_nodes, edges, grown, boundary):
    """
    Build a tree inside each cluster, using only grown edges.

    Returns (order, parent_edge). order lists the nodes so that every node
    comes after its parent, and parent_edge[v] is the edge joining v to its
    parent (None for the root of each tree). Any tree that touches the
    boundary is rooted at the boundary.
    """
    adj = [[] for _ in range(n_nodes)]
    for e, (u, v) in enumerate(edges):
        if grown[e]:
            adj[u].append((v, e))
            adj[v].append((u, e))

    seen = [False] * n_nodes
    parent_edge = [None] * n_nodes
    order = []
    # start from the boundary, so trees that reach it are rooted there
    starts = [boundary] + [v for v in range(n_nodes) if v != boundary]
    for s in starts:
        if seen[s] or not adj[s]:
            continue
        seen[s] = True
        queue = deque([s])
        while queue:
            u = queue.popleft()
            order.append(u)
            for w, e in adj[u]:
                if not seen[w]:
                    seen[w] = True
                    parent_edge[w] = e
                    queue.append(w)
    return order, parent_edge


def other_end(edges, e, v):
    # the node at the other end of edge e from node v
    u, w = edges[e]
    return w if u == v else u


def peel(edges, order, parent_edge, defects, n_nodes):
    """
    Turn the grown clusters into a list of correction edges.

    Loop over the nodes in reversed(order), so each node is handled before
    its parent. For each node v:

    1. Get its parent edge, e = parent_edge[v]. If e is None, v is the root
       of its tree, so skip it with continue.
    2. If is_defect[v] is True, the error must be on edge e. So:
       append e to correction, set is_defect[v] to False, find the parent
       with other_end(edges, e, v), and flip whether the parent is a defect
       (is_defect[parent] = not is_defect[parent]).

    Then return correction.
    """
    is_defect = [False] * n_nodes
    for v in defects:
        is_defect[v] = True
    correction = []

    # go through the nodes backwards
    for v in reversed(order):
        e = parent_edge[v]

        # skip if the node has no parent
        if e is None:
            continue

        # add the edge if the node is a defect
        if is_defect[v]:
            correction.append(e)
            is_defect[v] = False

            # find the parent and flip its defect value
            parent = other_end(edges, e, v)
            is_defect[parent] = not is_defect[parent]

    return correction


def decode_repetition(syndrome, d):
    # full union find decode for the distance d repetition code
    n_nodes, edges, boundary = repetition_graph(d)
    defects = [int(i) for i in np.flatnonzero(syndrome)]
    _, grown = grow(n_nodes, edges, boundary, defects)
    order, parent_edge = spanning_forest(n_nodes, edges, grown, boundary)
    correction = np.zeros(d, dtype=bool)
    for e in peel(edges, order, parent_edge, defects, n_nodes):
        correction[e] = True
    return correction