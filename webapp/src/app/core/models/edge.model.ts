export interface Edge {
    key?: string;

    source: string;
    edge: string;
    target: string;
    weight: number;
    bio: number;
    mrho: number;
    is_passive: boolean;
    connection_metadata: string[];
    articles: string[];
    //old
    ref: string;
}