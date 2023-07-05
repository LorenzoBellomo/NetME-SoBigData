import numpy as np


class PageRankApproximate:
    # CONSTRUCTOR
    def __init__(self, alpha=0.85, max_iteration=1000, tol=1e-6):
        # APPROXIMATE PAGE RANK PARAMETERS
        self.alpha     = alpha
        self.max_iter  = max_iteration
        self.tol       = tol
        # NODES INDEXING
        self.nodes_idx = {}
        self.idx_nodes = {}
        # PAGE RANKS ELEMENTS TO WORK
        self.adj_mat   = None
        self.deg_vet   = None
        self.page_rank = None

    # FUNCTION USED TO CREATE A INDEX MAP ON NETWORK NODES
    # IT WILL BE USED TO MAKE A FAST PAGE RANK
    def _nodes_index_creation(self, network):
        for node_idx, node_key in enumerate(network.nodes):
            self.nodes_idx[node_key] = node_idx
            self.idx_nodes[node_idx] = node_key

    # WEIGHTED ADJACENT MATRIX CONSTRUCTION
    def _adjacent_matrix_construction(self, network):
        nodes_number = len(self.nodes_idx)
        adjacent_mtx = np.zeros((nodes_number, nodes_number), dtype=float)
        for src, dsts_edges_id in network.adj_list.items():
            src_idx  = self.nodes_idx[src]
            for dst, edge_id in dsts_edges_id:
                dst_idx  = self.nodes_idx[dst]
                score    = network.edges[edge_id].weight
                adjacent_mtx[src_idx, dst_idx] = score
        self.deg_vet = np.sum(adjacent_mtx, axis=1)
        self.adj_mat = adjacent_mtx

    # PAGERANK INITIALIZATION
    def _init_pagerank(self, network, n):
        pagerank = np.zeros(n, dtype=float)
        for node_key, node_id in self.nodes_idx.items():
            pagerank[node_id] = network.nodes[node_key].size
        self.page_rank = pagerank

    def approximate_pagerank_computing(self, network):
        self._nodes_index_creation(network)
        self._adjacent_matrix_construction(network)
        n = self.adj_mat.shape[0]
        self._init_pagerank(network, n)

        for i in range(self.max_iter):
            prev_pagerank   = self.page_rank.copy()
            # multiply by the adjacency matrix and damping factor
            self.page_rank  = self.alpha * self.adj_mat.dot(self.page_rank)
            # add the teleportation probability
            self.page_rank += (1 - self.alpha) * np.ones(n) / n
                   # tutti 0 tranne un 1 che corrisponde al nodo dove vi stiamo centrando (nodo della query)
                   # 1/k se sono k nodi indicati nella query
            # normalize to ensure the sum is 1
            self.page_rank /= np.sum(self.page_rank)
            # check for convergence
            if np.linalg.norm(self.page_rank - prev_pagerank) < self.tol:
                break

        for node_idx, pagerank in enumerate(self.page_rank):
            network.nodes[self.idx_nodes[node_idx]].pagerank = pagerank

        # SORTING NODE
        network.nodes = {
            k: v for k, v in sorted(network.nodes.items(), key=lambda item: item[1].pagerank, reverse=True)
        }
