class BFSGroupNodes:
    def __init__(self):
        self.nodes            = []
        self.cumulative_score = []

    # USED FOR ROOT NODE
    def node_init(self, node_key):
        self.nodes.append(node_key)

    # USED FOT NO ROOT NODE
    def add_node(self, node_key, edge_key, network):
        self.nodes.append(node_key)
        score = network.nodes[node_key].size * network.edges[edge_key].weight
        self.cumulative_score.append(score)

    def __copy__(self):
        new_node                  = BFSGroupNodes()
        new_node.nodes            = self.nodes.copy()
        new_node.cumulative_score = self.cumulative_score.copy()
        return new_node

    def score_computing(self):
        self.cumulative_score = sum(self.cumulative_score) / len(self.cumulative_score)


class BFsDJK:
    def __init__(self, network):
        self.network   = network
        self.nodes_seq = []

    # THIS FUNCTION HAS BEEN DEFINED FOR BUILDING NODE'S BFS.
    # WE CONSIDER:
    #     - TWO DEPTH LEVELS IF THE NUMBER OF SELECTED NODES IS HIGHER THAN 300,
    #     - A HIGHER DEPTH ONE IN ORDER TO COLLECT A MAX NUMBER OF PRINTABLE NODES BY GUI
    # node_pos: ALLOWS TO SELECT THE STARTING NODE. IF NONE THEN THE NODE WITH HIGHER FREQUENCY IS SELECTED
    def node_bfs(self, node_pos = None):
        nodes              = set()
        if not node_pos:
            node_pos       = next(iter(self.network.nodes))
        nodes.add(node_pos)
        bfs_seq_nodes      = BFSGroupNodes()
        bfs_seq_nodes.node_init(node_pos)
        iteration_elem     = [(bfs_seq_nodes, self.network.adj_list[node_pos])]
        new_iteration_elem = []
        while len(iteration_elem) != 0 and len(nodes) < 300:
            print(nodes)
            for bfs_node, children in iteration_elem:
                for node_key, edge_key in children:
                    nodes.add(node_key)
                    node_copy = bfs_node.__copy__()
                    node_copy.add_node(node_key, edge_key, self.network)
                    if node_key not in self.network.adj_list:
                        self.nodes_seq.append(node_copy)
                        continue
                    adj_nodes  = self.network.adj_list[node_key]
                    new_iteration_elem.append((node_copy, adj_nodes))
            iteration_elem     = new_iteration_elem
            new_iteration_elem = []
        self.nodes_seq += [node[0] for node in iteration_elem]
        for node in self.nodes_seq:
            node.score_computing()
        self.nodes_seq = sorted(self.nodes_seq, key=lambda x: x.cumulative_score, reverse=True)
        selected_node  = []
        for macro_node in self.nodes_seq:
            for node in macro_node.nodes:
                if node in selected_node: continue
                selected_node.append(node)
        final_node     = {}
        for node_key in selected_node:
            final_node[node_key] = self.network.nodes.pop(node_key)
        self.network.nodes       =  {**final_node, **self.network.nodes}