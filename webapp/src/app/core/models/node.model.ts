/*  NODE INTERFACE
 *  Such a Node interface is used to represent a node in the graph.
 *    - key            : the key of the node
 *    - word           : the word of the node (is printed on the graph)
 *    - categories     : list of biological categories of the node
 *    - spots          : list of spots under this node
 *    - pagerank       : pagerank of the node
 *    - count          : frequency of the node
 *    - categoriesNames: biological categories concatenated with a semi-colon
 */
export interface Node {
     key?           : string;
     word           : string;
     categories     : string[];
     spot           : string[];
     pagerank       : number;
     count          : number;
     categoriesNames: string;
     data           : any;
}

export class WordSpot {
    word      : string;
    spot      : string;
    categories: string[];
    pagerank  : number;
    constructor(node, spot) {
        this.word       = node.word;
        this.spot       = spot;
        this.categories = node.categories;
        this.pagerank   = node.pagerank;
    }
}
