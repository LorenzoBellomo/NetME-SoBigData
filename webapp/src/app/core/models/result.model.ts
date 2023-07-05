import { Edge } from "./edge.model";
import { Node } from "./node.model";

export interface Result {
    nodes: Node[]
    edges: Edge[]
    sentences: { [article_key: string]: ResultSentence[] }
}

export interface ResultSentence {
    title: string;
    text: string;
    disease: string[];
    specie: string[];
    start_pos: number;
    end_pos: number;
    edges?: string[];
    edges_new?: Map<string, EdgeSentence>;
}

export interface EdgeSentence {
    source : number[]
    target : number[]
    act_pos: number[][]
}

export interface NetResult {
    net: any[];
    edgeslist: { [key: string]: Edge[] };
}
