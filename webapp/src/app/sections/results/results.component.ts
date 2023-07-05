import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { HighlightDialogComponent } from '../../shared/highlight-dialog/highlight-dialog.component';
import * as cytoscape from 'cytoscape';
import * as svg from 'cytoscape-svg';
import * as popper from 'cytoscape-popper';
import fcose from 'cytoscape-fcose';
import spread from 'cytoscape-spread';
cytoscape.use(spread);
cytoscape.use(fcose);
cytoscape.use(popper);
cytoscape.use(svg);
import { MatTableDataSource } from '@angular/material/table';
import { Edge } from '../../core/models/edge.model';
import { Node } from '../../core/models/node.model';
import { ResultsService } from './results.service';
import { ResponseType } from '../../core/models/enums';
import { ActivatedRoute } from '@angular/router';
import { takeUntil } from 'rxjs/operators';
import { BehaviorSubject, Subject } from 'rxjs';
import { ConsoleComponent } from './console/console.component';
import { trigger, transition, style, animate } from '@angular/animations';
import { MatExpansionPanel } from '@angular/material/expansion';
import {EdgeSentence, NetResult, ResultSentence} from 'src/app/core/models/result.model';
import { Category } from 'src/app/core/models/category.model';
import { ConfigMessage } from 'src/app/core/models/config-message.model';


@Component({
	selector: 'app-results',
	templateUrl: './results.component.html',
	styleUrls: ['./results.component.css'],
	animations: [trigger('fadeIn', [transition(':enter', [style({ opacity: 0 }), animate('0.2s ease-out', style({ opacity: 1 }))])])]
})
export class ResultsComponent implements OnInit, OnDestroy {

	minRho: number = 0; // [0,1]
	maxItems: number = 50; //TODO
	itemsCount: number = 50; //TODO
	minWeight: number = 0; // [0,1]
	bioCoherence: number = 0; // [0,1]

	@ViewChild('graph', { static: false }) graph: ElementRef | undefined
	@ViewChild('console', { static: false }) consoleComponent: ConsoleComponent | undefined
	@ViewChild('panelAnalysis', { static: false }) panelAnalysis: MatExpansionPanel | undefined;
	@ViewChild('panelDetails', { static: false }) panelDetails: MatExpansionPanel | undefined;
	disableAnimation: boolean = true


	cy: cytoscape.Core | undefined;

	detailInfo: "empty" | "node" | "edge" = "empty"
	dataSourceEdge = new MatTableDataSource<any>();
	tableColumnsEdge: string[] = ['edge', 'weight', 'bio', 'articles'];
	dataSourceNode = new MatTableDataSource<any>();
	tableColumnsNode: string[] = ['edge', 'nodes', 'articles'];

	loading: boolean = true
	response: boolean = false

	console: boolean = false

	lastConsoleMessage: BehaviorSubject<string>;
	resultReady: boolean = false

	error: boolean = false
	errorMessage1: string = ''
	errorMessage2: string = ''

	id: string = ''

	layouts: { value: string, name: string }[] = [
		{ value: 'fcose', name: 'fCoSE' },
		{ value: 'spread', name: 'Spread' },
		{ value: 'concentric', name: 'Concentric' }
	]
	currentLayout = 'fcose'

	userHiddenNodes: Set<string> = new Set()

	private _unsubscribeAll: Subject<any>;

	analysisRoot: { sourceNode: Node | undefined, targetNode: Node | undefined, cyRootNode: any, cyTargetNode: any } = {
		cyRootNode: null,
		cyTargetNode: null,
		sourceNode: undefined,
		targetNode: undefined
	}
	analysisMessage: string = 'Currently no analysis applied.'
	analysisItems: BehaviorSubject<any[]> = new BehaviorSubject([] as any[])
	selectedAnalysisTab: number = 0
	selectedAnalysisOpt: { value: string, label: string, hasSource: boolean, hasTarget: boolean, hasTable: boolean } | undefined
	analysisColumn: Map<string, any> = new Map()

	configMessages: ConfigMessage[] = []

	constructor(public dialog: MatDialog, public resultsService: ResultsService, private activatedRoute: ActivatedRoute) {
		this.lastConsoleMessage = new BehaviorSubject('')
		this._unsubscribeAll = new Subject()
		this.id = activatedRoute.snapshot.paramMap.get('id') || ""
		this.resultsService.queryResult(this.id).subscribe(() => { })
	}

	ngOnInit(): void {
		this.loading = true

		this.resultsService.resultObserver.pipe(takeUntil(this._unsubscribeAll)).subscribe(async (v: ResponseType) => {
			if (!v || v === "NONE") return

			this.loading = false
			this.response = false
			this.console = false
			this.error = false

			switch (v) {
				case "CONSOLE":
					this.console = true

					this.resultsService.getConsoleWS(this.id).pipe(takeUntil(this._unsubscribeAll)).subscribe(s => {
						this.lastConsoleMessage.next(s)
						this.consoleComponent?.scrollToBottom()
						if (s.includes("END ELABORATION")) {
							this.resultsService.closeWS()
							this.resultsService.resultObserver.next("NONE")
							this.resultReady = true
						}
						else if (s.includes("ERROR")) {
							this.resultsService.closeWS()
							this.resultsService.resultObserver.next("NONE")
							this.console = false
							this.error = true
							this.errorMessage1 = 'Error occurred'
							this.errorMessage2 = 'The server did not response correctly. Please retry later.<br>'+s.split("||")[0]
						}
					})
					break
				case "RESPONSE":
					this.response = true
					setTimeout(() => {
						this.onToggleCategory(this.resultsService.categories)
						this.createGraph()
						this.resultsService.resultObserver.next("NONE")
						this.disableAnimation = false
					}, 1000)
					break
				case "NOT_FOUND":
					this.error = true
					this.errorMessage1 = 'Result not found'
					this.errorMessage2 = 'There is not result for this id.'
					break
				case "ERROR":
					this.error = true
					this.errorMessage1 = 'Error occurred'
					this.errorMessage2 = 'The server did not response correctly. Please retry later.'
					break
			}
		})

		this.configMessages = (this.activatedRoute.snapshot.data['t1'] as ConfigMessage[] || [])
		console.log(this.configMessages)
	}

	ngOnDestroy(): void {
		this.resultsService.closeWS()
		this.resultsService.resultObserver.next("NONE")

		this._unsubscribeAll.next()
		this._unsubscribeAll.complete()
	}

	viewResult() {
		this.loading = true
		this.resultsService.queryResult(this.id).subscribe(() => { })
	}

	private createGraph() {
		const net: NetResult = this.resultsService.makeNet(this.maxItems, this.minWeight, this.bioCoherence, this.userHiddenNodes)

		this.cy = cytoscape({
			container: this.graph!.nativeElement,
			elements: net.net,
			minZoom: 0.05,
			maxZoom: 50,

			style: [
				{
					selector: 'node',
					style: {
						'background-color': 'data(color)',
						'label': 'data(name_t)',
						'width': 'data(size)',
						'height': 'data(size)',
					}
				},
				{
					selector: 'edge',
					style: {
						'width': 2,
						'line-color': '#ccc',
						'target-arrow-color': '#ccc',
						'target-arrow-shape': 'triangle',
						'curve-style': 'bezier',
					}
				},
				{
					selector: ':selected',
					css: {
						'background-color': '#145689',
						'line-color': '#00b3b9',
						'target-arrow-color': '#00b3b9',
						'source-arrow-color': '#00b3b9'
					}
				}
			],
			layout: this.getLayoutOptions()
		});

		this.cy.on('tap', (event: any) => {
			if (event.target === this.cy) this.detailInfo = "empty"
			else {
				if ('source' in event.target.data()) { //EDGE
					let edge_hash = this.resultsService.hashEdge(event.target.data().source, event.target.data().target);
					this.displayEdges(net.edgeslist[edge_hash]);
					this.showNodeEdgeDetails()
					this.detailInfo = "edge"
				} else { //NODE
					if (this.resultsService.nodesMap.has(event.target.data().key)) {
						const name = this.resultsService.nodesMap.get(event.target.data().key)?.word
						this.displayNodes(name!, net.edgeslist);
						this.showNodeEdgeDetails()
						this.detailInfo = "node"
					}
				}
			}
		});

		this.cy.elements().unbind("mouseover");
		this.cy.elements().bind("mouseover", (event) => {
			if (!this.isTarget) {
				this.isTarget = event.target
				setTimeout(() => {
					if (this.isTarget === event.target) {
						event.target.popperRefObj = event.target.popper({
							content: () => {
								let content = document.createElement("div");
								content.classList.add("popper-div");
								content.innerHTML = event.target.data().name ?? event.target.data().edge;
								document.body.appendChild(content);
								return content;
							},
						})
					} else this.destroyTip(event)
				}, 50)
			} else this.destroyTip(event)
		});

		this.cy.elements().unbind("mouseout");
		this.cy.elements().bind("mouseout", (event) => {
			this.destroyTip(event)
		});
	}
	isTarget = null;

	private destroyTip(event: any) {
		if (this.isTarget && (this.isTarget as any).popperRefObj) {
			(this.isTarget as any).popperRefObj.state.elements.popper.remove();
			(this.isTarget as any).popperRefObj.destroy();
		}
		if (event.target.popperRefObj) {
			event.target.popperRefObj.state.elements.popper.remove();
			event.target.popperRefObj.destroy();
		}
		this.isTarget = null
	}

	changeLayout(v: string) {
		const layout = this.cy!.layout(this.getLayoutOptions())
		layout.run()
	}

	private getLayoutOptions() {
		return {
			name: this.currentLayout,
			fit: true, // whether to fit the viewport to the graph
			spacingFactor: 2.0,
			padding: 5, // the padding on fit
			minNodeSpacing: 10,
			animate: false,

			nodeSeparation: 1,
			idealInterClusterEdgeLengthCoefficient: 1.4,
			allowNodesInsideCircle: false,
			maxRatioOfNodesInsideCircle: 0.1,
			springCoeff: 0.05,
			nodeRepulsion: 20000,
			/*name: 'cise',
			refresh: 10,
			animationDuration: undefined,
			animationEasing: undefined,
			fit: false,
			padding: 5,
			nodeSeparation: 1,
			idealInterClusterEdgeLengthCoefficient: 1.4,
			allowNodesInsideCircle: false,
			maxRatioOfNodesInsideCircle: 0.1,
			springCoeff: 0.05,
			nodeRepulsion: 20000,
			gravity: 0.25,
			gravityRange: 3.8, */
			/* name: 'cose',
			idealEdgeLength: 100,
			nodeOverlap: 20,
			refresh: 20,
			fit: true,
			padding: 30,
			randomize: false,
			componentSpacing: 100,
			nodeRepulsion: 400000,
			edgeElasticity: 100,
			nestingFactor: 5,
			gravity: 80,
			numIter: 1000,
			initialTemp: 200,
			coolingFactor: 0.95,
			minTemp: 1.0 */
		}
	}

	resetZoom() {
		if (this.cy)
			this.cy.fit()
	}

	onToggleViewClicked(e: [number, boolean]) {
		this.resultsService.annotationList[e[0]].show = e[1]

		if (e[1]) this.userHiddenNodes.delete(this.resultsService.annotationList[e[0]].word)
		else this.userHiddenNodes.add(this.resultsService.annotationList[e[0]].word)

		this.createGraph()
	}

	onFocusViewClicked(e: string) {
		const node = this.getCyNode(e)

		if (!!node) {
			const k = (this.maxItems / 20.0)
			const level = Math.max(Math.min(k, 3), 2)
			this.resetZoom()
			this.cy!.animate({
				zoom: {
					level: level,
					position: node.position()
				},
				pan: node.position(),
				duration: 250,
				easing: 'ease-out'
			})
		}
	}

	onToggleCategory(categories: Category[]) {
		this.resultsService.categories = categories
		const activeCategories = new Set(this.resultsService.categories.filter(c => c.show).map(c => c.name))

		this.resultsService.annotationList.forEach((e, i, a) => {
			this.resultsService.annotationList[i].show = false

			if (this.resultsService.nodesMap.has(e.key)) {
				(this.resultsService.nodesMap.get(e.key)?.categories || []).forEach(category => {
					if (activeCategories.has(category))
						this.resultsService.annotationList[i].show = true
				})
			}
		})

		this.createGraph()
	}


	onChangeMaxItems() {
		this.createGraph()
	}

	onChangeMinWeight() {
		this.createGraph()
	}

	onChangeBioCoherence() {
		this.createGraph()
	}

	parseFixed(elem: string, len: number): string {
		return parseFloat(elem).toFixed(len)
	}

	private displayEdges(edgeslist: Edge[]) {
		this.dataSourceEdge.data = edgeslist
	}

	private displayNodes(node: string, edgelist: { [key: string]: Edge[] }) {
		let items: any[] = []
		for (let target of Object.keys(edgelist)) {
			edgelist[target].forEach((t: Edge) => {
				if (t.source === node) {
					items.push({
            key      : t.key,
						edge     : t.edge,
						target   : t.target,
						src      : t.source,
						articles : t.articles,
						bio      : t.bio,
						source   : true
					})
				} else if (t.target === node) {
					items.push({
            key      : t.key,
						edge     : t.edge,
						target   : t.source,
						src      : t.target,
						articles : t.articles,
						bio      : t.bio,
						source   : false
					})
				}
			})
		}
		this.dataSourceNode.data = items
	}

	clickEdgeLink(elem: Edge) {
		this.linkClicked(elem.key!, '1')
	}


  sentenceTextCreation(shift:number, sentence: string, position: number[], c1) {
      const spos: number = position[0] + shift
      const epos: number = position[1] + shift
      let   word: string = sentence.substring(spos, epos)
            word         = `<span style="background-color: ${c1}">${word}</span>`
      sentence     = sentence.substring(0, spos) + word + sentence.substring(epos)
      return {"sentence":sentence, "shift":shift + word.length - (position[1] - position[0])}
  }


	clickNodeLink(article: string, element: Edge) {
		const sentences: ResultSentence[] = this.resultsService.getSentencesForEdge(article, element)
		let html = ""
		html += "<b>Article " + article + "</b><br><br>"
		const source = (element as any).src
		const c1 = this.resultsService.getCategoryColor(source)
		const c2 = this.resultsService.getCategoryColor(element.target)

    sentences.forEach(s => {
			  if (element.key && s.edges_new){
            const edgeSentence = s.edges_new[element.key]
            if(!edgeSentence) return
            let sentence = s.text
            let shf: number = 0
            let res = this.sentenceTextCreation(shf, sentence, edgeSentence.source, c1)
            sentence = res.sentence; shf = res.shift
            edgeSentence.act_pos.forEach((pos: number[]) => {
            res = this.sentenceTextCreation(shf, sentence, pos, "highlight")
                sentence = res.sentence; shf = res.shift
            })
            res = this.sentenceTextCreation(shf, sentence, edgeSentence.target, c2)
            sentence = res.sentence
            html += "<i>" + sentence + "</i><br><hr><br>";
        }
    })

		this.dialog.open(HighlightDialogComponent, {
			maxWidth: '800px',
			data: { innerHTML: html, label: element.target }
		})
	}

	linkClicked(id: string, table: string) {
		if (table === '0') {
			window.open(this.resultsService.articlesMap.get(id)?.link, '_blank')
		} else if (table === '1') {
			let html = ""
			let sentences = this.resultsService.edgesSentenceMap.get(id)!
			let element = this.resultsService.edgesMap.get(id)!
			const c1 = this.resultsService.getCategoryColor(element.source)
			const c2 = this.resultsService.getCategoryColor(element.target)

      const articles_idx: Map<string, number[]> = new Map<string, number[]>()
			if (!!sentences)
				sentences.forEach(s => {
          const sentence_data: ResultSentence = this.resultsService.sentencesMap.get(s.article)![s.index]
          if(!articles_idx.has(s.article))
              articles_idx.set(s.article, [])
          if(articles_idx.get(s.article)!.indexOf(s.index) === -1) {
              articles_idx.get(s.article)!.push(s.index)
              html += "<b>Article " + s.article + "</b><br><br>"
              const text     = this.resultsService.sentencesMap.get(s.article)![s.index].text
              let   sentence = ""
              if(element.key && sentence_data.edges_new) {
                 const edgeSentence = sentence_data.edges_new[element.key]
                 sentence = text
                 let shf: number = 0
                 let res = this.sentenceTextCreation(shf, sentence, edgeSentence.source, c1)
                 sentence = res.sentence; shf = res.shift
                 edgeSentence.act_pos.forEach((pos: number[]) => {
                    res = this.sentenceTextCreation(shf, sentence, pos, "highlight")
                    sentence = res.sentence; shf = res.shift
                 })
                 res = this.sentenceTextCreation(shf, sentence, edgeSentence.target, c2)
                 sentence = res.sentence
              }
              html += "<i>" + sentence + "</i><br><hr><br>";
          }
				})

			this.dialog.open(HighlightDialogComponent, {
				maxWidth: '800px',
				data: { innerHTML: html, label: element.edge }
			})
		}
	}

	downloadSvg() {
		var svgContent = (this.cy as any).svg({ scale: 1, full: true, bg: '#fff' });
		var blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
		var url = URL.createObjectURL(blob);
		var link = document.createElement("a");
		link.download = "graph.svg";
		link.href = url;
		link.click();
	}

  downloadJSON(){
      const dump_json = JSON.stringify(this.resultsService.dump, null, 4);
      const element   = document.createElement('a');
      element.setAttribute('href', "data:text/json;charset=UTF-8," + encodeURIComponent(dump_json));
      element.setAttribute('download', this.id + ".json");
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click(); // simulate click
      document.body.removeChild(element);
  }

	downloadCsv() {
		let nodesContent = 'data:text/csv;charset=utf-8,';
		let edgesContent = 'data:text/csv;charset=utf-8,';
		//Nodes

		let colAnalysisNode = ''
		if (this.analysisItems.value.length > 0)
			colAnalysisNode = ';' + this.analysisMessage.replace("analysis.", "analysis")

		nodesContent += 'node;categories;count;pagerank' + colAnalysisNode + '\n';
		this.resultsService.nodesItems.value.forEach((n: Node) => {
			nodesContent += n.word + ";" + n.categoriesNames + ";" + n.count + ";" + n.pagerank +
				(this.analysisColumn.has(n.word!) ? ';' + this.analysisColumn.get(n.word!) : '') + "\n";
		})
		var encodedNodes = encodeURI(nodesContent);
		var nodesDownloadLink = document.createElement("a");
		nodesDownloadLink.setAttribute("href", encodedNodes);
		nodesDownloadLink.setAttribute("download", "nodes.csv");
		document.body.appendChild(nodesDownloadLink);
		nodesDownloadLink.click();
		//Edges
		edgesContent += 'source;target;edge;weight;bio;articles\n';
		this.resultsService.edgesItems.value.forEach((e: Edge) => {
			edgesContent += e.source + ";" +
				e.target + ";" +
				e.edge + ";" +
				e.weight + ";" +
				e.bio + ";" +
				e.ref + "\n";
		})
		var encodedEdges = encodeURI(edgesContent);
		var edgesDownloadLink = document.createElement("a");
		edgesDownloadLink.setAttribute("href", encodedEdges);
		edgesDownloadLink.setAttribute("download", "edges.csv");
		document.body.appendChild(edgesDownloadLink);
		edgesDownloadLink.click();
	}

	showNodeEdgeDetails() {
		this.panelDetails!.open()
	}


	private getCySelector(): string {
		return '[id = "' + this.analysisRoot?.sourceNode?.word as cytoscape.Selector + '"]'
	}

	private getCyNode(target: string) {
		const nodes: any[] = (this.cy!.filter((element: any) => {
			return element.isNode() && element.data().name === target;
		})) as unknown as any[]
		return nodes.length > 0 ? nodes[0] : null
	}

	private showAnalysisError() {
		this.analysisMessage = 'Cannot execute analysis.'
	}

	startTraversing() {
		this.analysisMessage = this.selectedAnalysisOpt?.label + ' analysis for ' + this.analysisRoot?.sourceNode?.word

		if (this.selectedAnalysisOpt?.value === 'components') {
			const co = this.analysisRoot?.cyRootNode.components()
			if (co) co.forEach(c => c.select())
			else this.showAnalysisError()

		}
		else if (this.selectedAnalysisOpt?.value === 'neighborhood') this.analysisRoot?.cyRootNode.neighborhood().select()
	}

	startSearch() {
		const opt = { root: this.getCySelector(), visit: (v, _e, _u, _i, depth) => {
			console.log( 'visit ' + (depth < 3) );
			//return depth < 3;
			// TODO check depth parameter
		  }, } as cytoscape.SearchFirstOptions

		this.analysisMessage = this.selectedAnalysisOpt?.label + ' analysis from ' + this.analysisRoot?.sourceNode?.word

		if (this.selectedAnalysisOpt?.value === 'bfs') this.cy!.elements().bfs(opt).path.select()
		else if (this.selectedAnalysisOpt?.value === 'dfs') this.cy!.elements().dfs(opt).path.select()
		else if (this.selectedAnalysisOpt?.value === 'dij') {
			const di = this.cy!.elements().dijkstra(opt as cytoscape.SearchDijkstraOptions)
			if (!!di) {
				di.pathTo(this.analysisRoot?.cyTargetNode).select()
				this.analysisMessage += ' to ' + this.analysisRoot?.targetNode?.word
			}
			else this.showAnalysisError()
		}
	}

	startCentrality() {
		const opt = { root: this.getCySelector() } as cytoscape.SearchFirstOptions

		if (this.selectedAnalysisOpt?.value === 'bet') {
			const bc = this.cy!.elements().betweennessCentrality(opt as cytoscape.SearchBetweennessOptions)
			this.analysisItems.next(this.cy!.nodes().map((e: any) => {
				return { value: parseFloat((bc.betweenness(e)).toFixed(4)), word: e.data('name') }
			}))
		}
		else if (this.selectedAnalysisOpt?.value === 'pr') {
			const pg = this.cy!.elements().pageRank(opt as cytoscape.SearchPageRankOptions)
			if (pg) {
				this.analysisItems.next(this.cy!.nodes().map((e: any) => {
					return { value: parseFloat((pg.rank(e)).toFixed(4)), word: e.data('name') }
				}))
			}
			else this.showAnalysisError()
		}

		this.analysisItems.value.forEach(e => this.analysisColumn.set(e['word'], e['value']))
	}

	startClustering() {
		const k = Math.max(Math.floor(this.resultsService.nodesItems.value.length / 10), 1)
		let clusters: cytoscape.CollectionReturnValue = {} as cytoscape.CollectionReturnValue

		if (this.selectedAnalysisOpt?.value === 'markov') clusters = (this.cy!.elements() as any).markovClustering()
		else if (this.selectedAnalysisOpt?.value === 'kmeans') clusters = (this.cy!.elements() as any).kMeans(
			{
				k: k,
				attributes: [(node: any) => node.data('size')]
			}
		)
		else if (this.selectedAnalysisOpt?.value === 'hierical') clusters = (this.cy!.elements() as any).hierarchicalClustering(
			{
				k: k,
				attributes: [(node: any) => node.data('size')]
			}
		)

		let items: { name: string, color: string, count: number }[] = []

		for (var c = 0; c < clusters.length; c++)
			if (!!clusters[c]) {
				const name = 'Cluster ' + (c + 1)
				const color = this.resultsService.rainbow(clusters.length, c)
				clusters[c].style('background-color', color)
				items.push({ name: name, color: color, count: clusters[c].size() })

				clusters[c].forEach(e => {
					this.analysisColumn.set(e.data('name'), name)
				})
			}

		this.analysisItems.next(items)
	}

	clearAnalysis() {
		this.analysisRoot = { sourceNode: undefined, targetNode: undefined, cyRootNode: null, cyTargetNode: null }
		this.clearResult()
		this.analysisItems.next([])
		this.analysisColumn.clear()
	}

	clearResult(val?: string) {
		const index = this.resultsService.analysisOptions[this.selectedAnalysisTab].options.findIndex(o => o.value === val)
		if (index > -1) this.selectedAnalysisOpt = this.resultsService.analysisOptions[this.selectedAnalysisTab].options[index]
		else this.selectedAnalysisOpt = undefined

		this.analysisItems.next([])
		this.analysisColumn.clear()
		// this.cy!.elements().deselect()
		// this.analysisResult = -1
	}

	startAnalysisAlgo() {
		this.analysisColumn.clear()
		this.cy!.elements().deselect()
		this.analysisMessage = this.selectedAnalysisOpt?.label + ' analysis.'

		switch (this.selectedAnalysisTab) {
			case 0: this.startTraversing(); break
			case 1: this.startSearch(); break
			case 2: this.startCentrality(); break
			case 3: this.startClustering(); break
		}
	}

	setAnalysisNode(node: Node, isRoot: boolean) {
		//this.clearResult()
		if (isRoot) {
			this.analysisRoot!.sourceNode = node
			this.analysisRoot!.cyRootNode = this.getCyNode(node.word!)
		}
		else {
			this.analysisRoot!.targetNode = node
			this.analysisRoot!.cyTargetNode = this.getCyNode(node.word!)
		}
	}

	getAnalysisTableColumns(): string[] {
		return this.selectedAnalysisTab === 3 ? ['name', 'color', 'count'] : ['word', 'value']
	}

	exportAnalysisTable() {
		const columns = this.getAnalysisTableColumns()
		let content = 'data:text/csv;charset=utf-8,'
		content += columns.reduce((acc, v) => acc + ';' + v)
		content += '\n'

		this.analysisItems.value.forEach(e => {
			for (let k of columns) content += '"' + e[k].toString().replace('#', '') + '";'
			content += '\n'
		})

		let encoded = encodeURI(content)
		let link = document.createElement("a")
		link.setAttribute("href", encoded)
		link.setAttribute("download", this.analysisMessage.replace(" analysis.", "") + ".csv")
		document.body.appendChild(link)
		link.click()
	}
}
