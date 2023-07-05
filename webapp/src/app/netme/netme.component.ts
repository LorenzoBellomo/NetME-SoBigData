import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import moment from 'moment';
import { ConfigMessage } from '../core/models/config-message.model';
import { RequestData } from '../core/models/request-data.model';
import { NetRESTService } from '../core/netrest.service';
import { SessionService } from '../core/session.service';

@Component({
	selector: 'app-netme',
	templateUrl: './netme.component.html',
	styleUrls: ['./netme.component.css']
})
export class NetmeComponent implements OnInit {

	searchOpts: { value: string, title: string }[] = [
		{ value: 'terms', title: 'Search from query terms' },
		{ value: 'ids', title: 'Search from specific Paper ID' },
	]
	searchTypesOpts: { value: string, title: string }[] = [
		{ value: 'full-text', title: 'Full Text Article (PMC)' },
		{ value: 'abstract', title: 'Abstract (PubMed)' },
	]
	papersOpts: { value: string, title: string }[] = [
		{ value: '10', title: '10' },
		{ value: '20', title: '20' },
		{ value: '50', title: '50' },
		{ value: '100', title: '100 (may take longer time)' },
		{ value: '500', title: '500 (may take longer time)' },
	]
	sortOpts: { value: string, title: string }[] = [
		{ value: 'relevance', title: 'Relevance' },
		{ value: 'date', title: 'Date' },
	]

	// default values
	searchOpt: string = 'terms'
	searchTypeOpt: string = 'full-text'
	paperOpt: string = '10'
	sortOpt: string = 'relevance'
	networkName: string = ''
	userNetworkName: string = ''

	tabs: string[] = ['pubmed', 'text', 'pdf']
	searchTab: string = 'pubmed'

	pubmedInput: string = ''
	freeTextInput: string = ''
	files: File[] = [];

	searching: boolean = false
	errorMessage1: string = ''
	errorMessage2: string = ''
	error: boolean = false

	configMessages: ConfigMessage[] = []

	constructor(private restService: NetRESTService, private _router: Router, private sessionService: SessionService, private activatedRoute: ActivatedRoute) { }

	ngOnInit(): void {
		this.initPage()

		this.configMessages = (this.activatedRoute.snapshot.data['t1'] as ConfigMessage[] || [])
		console.log(this.configMessages)
	}

	async startSearch() {
		this.searching = true

		let v: RequestData = {
			searchOn: this.searchOpt,
			searchType: this.searchTypeOpt,
			papersNumber: this.paperOpt,
			sortType: this.sortOpt,
			queryMode: this.searchTab,
			input: await this.getInput(),
			networkName: this.userNetworkName || this.networkName
		}

		this.restService.startSearch(v).subscribe(s => {
			if (!s || !s['query_id'] || (s && s['status'] && s['status'] === 500)) {
				this.error = true
				this.searching = false
				this.errorMessage1 = 'An error occurred.'
				this.errorMessage2 = 'Please retry later.'
				return
			}

			this.sessionService.saveSearch({
				searchId: s['query_id'],
				generatedOn: moment().format("YYYY-MM-DD HH:mm"),
				sources: v.queryMode === 'pdf' ? this.getFilesName() : v.input as string,
				description: "Query mode: " + v.queryMode,
				networkName: v.networkName
			})
			this._router.navigateByUrl('/results/' + s['query_id'])
		})
	}

	private getFilesName(): string {
		let s = ""
		this.files.forEach(f => s += f.name + ", ")

		return s.substr(0, s.length - 2)
	}

	toBase64 = file => new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.readAsDataURL(file);
		reader.onload = () => resolve(reader.result);
		reader.onerror = error => reject(error);
	});

	private async getInput(): Promise<string> {
		switch (this.searchTab) {
			case 'pubmed': return this.pubmedInput
			case 'text': return this.freeTextInput
			case 'pdf': {
				let serialized: any[] = []

				console.log(this.files.length)

				for (let f of this.files) {
					const base64 = await this.toBase64(f)
					serialized.push({ fname: f.name, data: base64 })
				}

				return JSON.stringify(serialized)
			}
			default: return ""
		}
	}

	fileChange(events: File[]) {
		this.files = events
	}

	fileRemoved(event: File) {
		this.files = this.files.filter(f => f.name !== event.name)
	}

	onTabChanged(index: number) {
		this.searchTab = this.tabs[index]
	}

	initPage() {
		this.errorMessage1 = ''
		this.errorMessage2 = ''
		this.error = false
		this.networkName = 'Network generated on ' + moment().format('YYYY-MM-DD HH:mm')
	}
}
