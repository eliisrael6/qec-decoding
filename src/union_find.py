"""
Union find structure for tracking clusters.

Each cluster is stored as a tree. Every node points to a parent, and the
node at the top of the tree (the one that is its own parent) is the root.
The root acts as the cluster's name, so two nodes are in the same cluster
exactly when they have the same root.
"""





class UnionFind:
    def __init__(self, n):
        # every node starts as its own cluster of size 1
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        """
        Return the root of the cluster containing x.

        1. Follow parent pointers from x until you reach a node that is
           its own parent. That node is the root.
        2. Path compression: walk the same path again and point every node
           on it straight at the root, so later finds are quicker.
        """
        root = x
        while self.parent[root] != root:
            root = self.parent[root]

        while self.parent[x] != x:
            next_node = self.parent[x]
            self.parent[x] = root
            x = next_node
        return root
        

    def union(self, a, b):
        """
        Merge the clusters containing a and b, and return the new root.

        1. Find the root of a and the root of b.
        2. If the roots are the same, a and b are already in one cluster,
           so return that root and stop.
        3. Otherwise put the root of the smaller cluster under the root of
           the larger one (if they are the same size, put b's root under
           a's), add the sizes together, and return the root on top.
        """
        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return ra

        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra

        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return ra