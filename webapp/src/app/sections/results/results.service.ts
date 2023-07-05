import { Injectable } from '@angular/core';
import { BehaviorSubject, from, Observable, of, Subject } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Edge } from '../../core/models/edge.model';
import { ArticleType, ResponseType } from '../../core/models/enums';
import { Article } from '../../core/models/link.model';
import {Node, WordSpot} from '../../core/models/node.model';
import { NetRESTService } from '../../core/netrest.service';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { environment } from 'src/environments/environment';
import { NetResult, Result, ResultSentence } from 'src/app/core/models/result.model';
import {collectionSnapshots} from "@angular/fire/firestore";


@Injectable({
    providedIn: 'root'
})
export class ResultsService {

    MAX_NODES: number = 300

    categories: { color: string, name: string, show: boolean }[] = [
        { color: '#ff4500', name: "biological pathway", show: true },
        { color: '#ffd700', name: "cell", show: true },
        { color: '#00ff00', name: "cell line", show: true },
        { color: '#dc143c', name: "cell type", show: true },
        { color: '#00ffff', name: "cellular component", show: true },
        { color: '#0000ff', name: "chemical entity", show: true },
        { color: '#adff2f', name: "compound", show: true },
        { color: '#ff7f50', name: "disease", show: true },
        { color: '#ff00ff', name: "drug", show: true },
        { color: '#1e90ff', name: "enzyme", show: true },
        { color: '#f0e68c', name: "gene", show: true },
        { color: '#90ee90', name: "gene variant", show: true },
        { color: '#add8e6', name: "physiological condition", show: true },
        { color: '#7b68ee', name: "protein", show: true },
        { color: '#228b22', name: "species", show: true },
        { color: '#7f0000', name: "symptom", show: true },
        { color: '#483d8b', name: "tissue", show: true },
        { color: '#b03060', name: "other", show: false }

        /*
          { color: '#ff4500', name: "mRNA", show: true },
          { color: '#ffd700', name: "miRNA", show: true },
          { color: '#00ff00', name: "lncRNA", show: true },
          { color: '#dc143c', name: "tRNA", show: true },
          { color: '#00ffff', name: "miscRNA", show: true },
          { color: '#00ffff', name: "rRNA", show: true },
          { color: '#00ffff', name: "snRNA", show: true },
          { color: '#00ffff', name: "snoRNA", show: true },
          { color: '#00bfff', name: "variant", show: true },
          { color: '#0000ff', name: "haplotype", show: true },
          { color: '#adff2f', name: "disease", show: true },
          { color: '#adff2f', name: "disorder", show: true },
          { color: '#ff7f50', name: "pathway", show: true },
          { color: '#ff00ff', name: "biological process", show: true },
          { color: '#1e90ff', name: "molecular function", show: true },
          { color: '#f0e68c', name: "role", show: true },
          { color: '#90ee90', name: "subatomic particle", show: true },
          { color: '#add8e6', name: "chemical entity", show: true },
          { color: '#7b68ee', name: "small molecule", show: true },
          { color: '#ee82ee', name: "cellular component", show: true },
          { color: '#ffc0cb', name: "biotech", show: true },
          { color: '#808080', name: "drug", show: true },
          { color: '#556b2f', name: "enzyme", show: true },
          { color: '#228b22', name: "transporter", show: true },
          { color: '#7f0000', name: "carrier", show: true },
          { color: '#483d8b', name: "endogenous retrovirus", show: true },
          { color: '#b8860b', name: "anatomical entity", show: true },
          { color: '#008b8b', name: "tissue", show: true },
          { color: '#00008b', name: "line cell", show: true },
          { color: '#8fbc8f', name: "cell", show: true },
          { color: '#b03060', name: "other", show: false }
         */
    ];

    categoriesIndexMap: Map<string, number> = new Map()

    analysisOptions: { label: string, selectLabel: string, options: { value: string, label: string, hasSource: boolean, hasTarget: boolean, hasTable: boolean }[] }[] =
        [
            {
                label: 'TRAVERSING',
                selectLabel: 'Select an algorithm',
                options: [
                    { value: 'neighborhood', label: 'Neighborhood', hasSource: true, hasTarget: false, hasTable: false },
                    { value: 'components', label: 'Connected components', hasSource: true, hasTarget: false, hasTable: false },
                ]
            },
            {
                label: 'SEARCH',
                selectLabel: 'Select an algorithm',
                options: [
                    { value: 'bfs', label: 'BFS', hasSource: true, hasTarget: false, hasTable: false },
                    { value: 'dfs', label: 'DFS', hasSource: true, hasTarget: false, hasTable: false },
                    { value: 'dij', label: 'Dijkstra', hasSource: true, hasTarget: true, hasTable: false },
                ]
            },
            {
                label: 'CENTRALITY',
                selectLabel: 'Select an algorithm',
                options: [
                    { value: 'bet', label: 'Betweenness centrality', hasSource: false, hasTarget: false, hasTable: true },
                    { value: 'pr', label: 'PageRank', hasSource: false, hasTarget: false, hasTable: true },
                ]
            },
            {
                label: 'CLUSTERING',
                selectLabel: 'Select an algorithm',
                options: [
                    { value: 'markov', label: 'Markov clustering', hasSource: false, hasTarget: false, hasTable: true },
                    { value: 'kmeans', label: 'kMeans', hasSource: false, hasTarget: false, hasTable: true },
                    { value: 'hierical', label: 'Hierarchical clustering', hasSource: false, hasTarget: false, hasTable: true },
                ]
            }
        ]


    articlesItems: BehaviorSubject<any> = new BehaviorSubject(null);
    articlesTableColumns: string[] = ['key', 'name'];
    articlesTableColumnsNames: string[] = ['Link', 'Article'];

    nodesItems: BehaviorSubject<Node[]>     = new BehaviorSubject([] as Node[]);
    nodesSpots: BehaviorSubject<WordSpot[]> = new BehaviorSubject([] as WordSpot[]);
    // nodesTableColumns: string[]          = ['word', 'categories', 'pagerank', 'spot', 'count'];
    nodesTableColumns: string[]             = ['word', 'spot', 'categories', 'pagerank'];

    edgesItems: BehaviorSubject<Edge[]> = new BehaviorSubject([] as Edge[]);
    edgesTableColumns: string[] = ['source', 'edge', 'target', 'weight', 'mrho', 'bio', 'ref'];

    annotationList: { key: string, word: string, show: boolean }[] = []
    annotationsItems: BehaviorSubject<any> = new BehaviorSubject(null);
    annotationsTableColumns: string[] = ['word', 'show', 'zoom']

    information: BehaviorSubject<any> = new BehaviorSubject(null);

    search: any = {}
    //data: any = {}
    nodesMap: Map<string, Node> = new Map()
    edgesMap: Map<string, Edge> = new Map()

    hiddenNodes: Set<string> = new Set()
    itemsCount: number = 0

    edgesSentenceMap: Map<string, { article: string, index: number }[]> = new Map()
    articlesMap: Map<string, Article> = new Map()

    sentencesMap: Map<string, ResultSentence[]> = new Map()


    resultObserver: BehaviorSubject<ResponseType> = new BehaviorSubject("NONE" as ResponseType);

    consoleMessages: string[] = []

    // DUMPS
    dump: any = null


    constructor(private restService: NetRESTService) {
        for (let i = 0; i < this.categories.length; i++)
            this.categoriesIndexMap.set(this.categories[i].name, i)
    }

    private socket$: WebSocketSubject<any> | undefined;
    private messagesSubject$ = new Subject();

    public connect(id: string): void {
        if (!this.socket$ || this.socket$.closed) {
            this.socket$ = this.getNewWebSocket(id);
            this.socket$.subscribe({
                next: (data) => {
                    this.messagesSubject$.next(data)
                },
                error: console.log,
                complete: () => console.log
            })
        }
    }

    private getNewWebSocket(id: string) {
        return webSocket({
            url: environment.wsURL + '/ws/' + id,
            deserializer: e => e.data
        })
    }

    sendMessage(msg: any) {
        this.socket$!.next(msg)
    }

    closeWS() {
        this.socket$?.complete()
    }

    getConsoleWS(id: string): Observable<string> {
        this.closeWS()
        console.log('new socket', id)
        this.socket$ = this.getNewWebSocket(id);
        this.socket$.subscribe({
            next: (data) => this.messagesSubject$.next(data),
            error: console.log,
            complete: () => console.log
        })
        return this.messagesSubject$.asObservable() as Observable<string>
    }

    queryResult(id: string): Observable<ResponseType> {
        return from(this.restService.querySearch(id))
            .pipe(switchMap(data => {

                if (data && data.status && data.status === 200) {
                    if (data.console_token) return this.consoleStatus(data)
                    else if (data.result) {
                        this.dump = data['result']
                        return this.resultStatus(this.dump)
                    }
                    return this.errorStatus()
                }
                else if (data && data.status && data.status === 404) {
                    return this.notFoundStatus()
                }
                else return this.errorStatus()
            }))
    }

    private consoleStatus(data: any): Observable<ResponseType> {
        this.consoleMessages = data.logs
        this.resultObserver.next("CONSOLE")
        return of("CONSOLE" as ResponseType)
    }

    private resultStatus(result: Result): Observable<ResponseType> {
        this.setResultInfo(result)
        this.setResultArticles(result)
        this.setResultNodes(result)
        this.setResultEdges(result)
        this.setResultSentences(result)
        this.setResultAnnotations(result)

        this.resultObserver.next("RESPONSE")
        return of("RESPONSE" as ResponseType)
    }

    private notFoundStatus(): Observable<ResponseType> {
        this.resultObserver.next("NOT_FOUND")
        return of("NOT_FOUND" as ResponseType)
    }

    private errorStatus(): Observable<ResponseType> {
        this.resultObserver.next("ERROR")
        return of("ERROR" as ResponseType)
    }

    private setResultInfo(data: any) {
        if (data.search_data) {
            this.information.next({
                description: data.search_data.description,
                created: data.search_data.created_on,
                updated: data.created_on
            })
            this.search = data.search_data
        }
    }

    private setResultArticles(data: any) {
        if (data.articles) {
            this.articlesMap = new Map(((data.articles || []) as string[]).map(v => this.createArticle(v)).map(v => [v.key, v]))
            this.articlesItems.next([...this.articlesMap.values()])
        }
    }

    private setResultNodes(result: Result) {
        this.nodesMap                = new Map()
        const nodes: Node[]          = [...result.nodes || []]
        const nodesSpots: WordSpot[] = []
        for (const node of result.nodes || []) {
            // node.word = node.spot //node.origin_word ? node.origin_word : node.spot
            node.categoriesNames = (node.categories || []).join(', ')
            this.nodesMap.set(node.key!, node)
            // SPOT-WORD CREATION FOR NODE TABLE IN GUI
            for (const spot of node.spot || []) {
                const spotWord= new WordSpot(node, spot)
                nodesSpots.push(spotWord)
            }
        }
        this.nodesItems.next(nodes)
        this.nodesSpots.next(nodesSpots)
    }

    private setResultEdges(result: Result) {
        this.edgesMap = new Map()
        const edges: Edge[] = [...result.edges || []]

        for (const edge of result.edges || []) {
            this.edgesMap.set(edge.key!, edge)
        }

        this.edgesItems.next(edges)
    }

    private setResultSentences(result: Result) {
        // doc_id: --> [sentence object]
        this.sentencesMap     = new Map()
        this.edgesSentenceMap = new Map()

        for (const key in result.sentences || {}) {
            const articles = result.sentences[key]
            this.sentencesMap.set(key, articles)

            for (let i = 0; i < articles.length; i++) {
                Object.keys(articles[i].edges_new || {}).forEach(e => {
                   if (!this.edgesSentenceMap.has(e)) this.edgesSentenceMap.set(e, [])
                   this.edgesSentenceMap.get(e)!.push({ article: key, index: i })
                })
            }
        }

        // EDGE ARTICLES CORRECTION
        this.edgesSentenceMap.forEach((articles, e) => {
            const documents: string[] = []
            articles.forEach(a => {
                if (!documents.includes(a.article)) documents.push(a.article)
            })
            this.edgesMap.get(e)!.articles = documents
        })
    }

    private setResultAnnotations(data: any) {
        this.annotationList = []
        this.nodesItems.value.forEach(n => {
            this.annotationList.push({ key: n.key!, word: n.word!, show: true })
        })
        this.annotationsItems.next(this.annotationList)
    }

    private createArticle(source: string): Article {
        let splitted = source.split("|")
        let article: Article = {
            type: splitted[0] as ArticleType,
            key: splitted[1],
            name: splitted[2],
            link: ''
        }

        switch (article.type) {
            case "freetext":
                article.key = "freetext"
                article.link = ''
                break;
            case "pdf":
                article.key = "PDF file"
                article.link = ''
                break;
            case "pmc":
                article.link = 'https://www.ncbi.nlm.nih.gov/pmc/articles/' + article.key.replace(/pmc/gi, '')
                break;
            case "pubmed":
                article.link = 'https://pubmed.ncbi.nlm.nih.gov/' + article.key.replace(/pubmed/gi, '')
                break;
        }

        return article
    }

    makeNet(_maxItems: number, _minWeight: number, _bioCoherence: number, userHiddenNodes: Set<string>): NetResult {
        let nodes: Node[] = []
        let edges: any[] = []
        let edgeslist: { [key: string]: Edge[] } = {}

        let maxItems     :number = _maxItems
        let minWeight    :number = _minWeight / 100.0
        let bioCoherence :number = _bioCoherence / 100.0
        let showed       :number = 0

        this.itemsCount = Math.min(this.nodesItems.value.length, this.MAX_NODES);

        // Filter nodes based on maxItems and minRho v.data.categories.includes('other') ||
        for (let v of this.nodesItems.value) {
            const index = this.annotationList.findIndex(t => t.word === v.word)

            if (index >= 0 && this.annotationList[index].show && userHiddenNodes.has(this.annotationList[index].word))
                this.annotationList[index].show = false

            if (showed >= maxItems || (index >= 0 && !this.annotationList[index].show)) {
                this.hideNode(v.word!)
            } else if (!userHiddenNodes.has(v.word!)) {
                showed++;
                this.showNode(v.word!)
            }
        }
        // Filter nodes
        this.nodesItems.value.forEach(v => {
            if (!this.hiddenNodes.has(v.word!)) {
                nodes.push({ ...v })
            }
        });
        // Filter edges
        this.edgesItems.value.forEach(v => {
            let edge_hash = this.hashEdge(v.source, v.target);
            if (!this.hiddenNodes.has(v.source) && !this.hiddenNodes.has(v.target)) {
                if (v.weight >= minWeight && v.bio > bioCoherence) {
                    if (!(edge_hash in edgeslist)) {
                        edges.push({ data: { ...v } })
                        edgeslist[edge_hash] = [];
                    }
                    edgeslist[edge_hash].push(v);
                }
            }
        });

        for (const n of nodes) {
            n.data = {
                id    : n.word,
                key   : n.key,
                size  : 10 + Math.sqrt(n.count) * 3,
                name  : n.word,
                name_t: n.word, //n.word!.length > 10 ? n.word?.substring(0, 8) + '…' : n.word,
                color : this.getCategoryColor(n.key!)
            }
        }

        return { net: [...nodes, ...edges], edgeslist: edgeslist };
    }

    private showNode(nodeId: string) {
        this.hiddenNodes.delete(nodeId)
    }

    private hideNode(nodeId: string) {
        this.hiddenNodes.add(nodeId)
    }

    getSentencesForEdge(article: string, e: Edge): ResultSentence[] {
        let set: Set<string> = new Set()
        let sentences: ResultSentence[] = []

        this.edgesSentenceMap.forEach((v: { article: string, index: number }[], k) => {
            const edge = this.edgesMap.get(k)

            if (edge?.edge === e.edge) {
                v.forEach(e => {
                    const k = e.article + e.index
                    if (article === e.article && !set.has(k)) {
                        sentences.push(this.sentencesMap.get(e.article)![e.index])
                        set.add(k)
                    }
                })
            }
        })
        return sentences
    }

    getCategoryColor(target: string): string {
        const other = this.categories[this.categories.length - 1]

        let validCategories = this.nodesMap.get(target)?.categories.filter(c => this.categoriesIndexMap.has(c)) || []

        if (validCategories.length === 0 || validCategories.length === 1 && validCategories[1] === other.name)
            return other.color

        return this.categories[this.categoriesIndexMap.get(validCategories[0]) || this.categories.length - 1].color
    }

    numberToColorHsl(i: number): string {
        var h = ((1 - i) * 1.2 * 100) / 360;
        var s = .8;
        var l = .7;
        var r, g, b;
        if (s == 0) {
            r = g = b = l;
        } else {
            function hue2rgb(p: any, q: any, t: any) {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1 / 6) return p + (q - p) * 6 * t;
                if (t < 1 / 2) return q;
                if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
                return p;
            }

            var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            var p = 2 * l - q;
            r = hue2rgb(p, q, h + 1 / 3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1 / 3);
        }
        return 'rgb(' + Math.floor(r * 255) + ',' + Math.floor(g * 255) + ',' + Math.floor(b * 255) + ')';
    }


    rainbow(numOfSteps: number, step: number): string {
        let r, g, b;
        let h = step / numOfSteps;
        let i = ~~(h * 6);
        let f = h * 6 - i;
        let q = 1 - f;
        switch (i % 6) {
            case 0: r = 1; g = f; b = 0; break;
            case 1: r = q; g = 1; b = 0; break;
            case 2: r = 0; g = 1; b = f; break;
            case 3: r = 0; g = q; b = 1; break;
            case 4: r = f; g = 0; b = 1; break;
            case 5: r = 1; g = 0; b = q; break;
        }
        let c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
        return c
    }

    private hashString(s: any) {
        var h = 0, l = s.length, i = 0;
        if (l > 0)
            while (i < l)
                h = (h << 5) - h + s.charCodeAt(i++) | 0;
        return h;
    };

    hashEdge(source: any, target: any) { //Return unique edge hash
        var list = [source, target];
        var res = list.join(' ');
        return this.hashString(res).toString();
    }
}
