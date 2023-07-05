import { Component, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort, MatSortable } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Observable } from 'rxjs';

@Component({
	selector: 'search-table',
	templateUrl: './search-table.component.html',
	styleUrls: ['./search-table.component.css']
})
export class SearchTableComponent implements OnInit {

	@Input() tableColumns: string[] = [];
	@Input() tableColumnsNames?: string[];
	@Input() items: Observable<any[]> = new Observable();
	@Input() linkIndex: number = -1;
	@Input() idIndex: number = -1;
	@Input() colorIndex: number = -1;
	@Input() hasOptions: boolean = true;
	@Input() showFocus: boolean = false;
	@Input() showNoData: boolean = true;
	@Input() class: string = ''; // or 'small'
	dataSource = new MatTableDataSource<any>();

	paginator: MatPaginator | undefined;

	@Input() hasAction: boolean = false;
	@Input() action: string = "Show/Hide";

	@Output() onLinkClicked: EventEmitter<string> = new EventEmitter();
	@Output() onToggleViewClicked: EventEmitter<[number, boolean]> = new EventEmitter();
	@Output() onFocusViewClicked: EventEmitter<string> = new EventEmitter();

	constructor() {
		if (!this.tableColumnsNames) this.tableColumnsNames = this.tableColumns;
	}

	@ViewChild(MatSort) set matSort(ms: MatSort) {
		this.dataSource.sort = ms;

		if (this.dataSource.data.length > 0 && this.dataSource.data[0].value !== undefined)
			setTimeout(() => this.dataSource.sort!.sort(({ id: 'value', start: 'desc' }) as MatSortable), 10)
	}

	@ViewChild(MatPaginator) set matPaginator(mp: MatPaginator) {
		this.dataSource.paginator = mp;
	}

	ngOnInit() {
		this.items?.subscribe(v => {
			if (!v) return

			// this.dataSource.paginator = this.paginator!;
			// this.dataSource.sort = this.sort!;
			this.dataSource.data = v.slice(0, 500) // TODO
		})
	}

	public doFilter = (value: string) => {
		this.dataSource.filter = value.trim().toLocaleLowerCase();
	}

	clickLink(id: string) {
		this.onLinkClicked.next(id)
	}

	toggleView(word: string) {
		const index = this.dataSource.data.findIndex((v: { word: string; }) => v.word === word)
		this.dataSource.data[index].show = !this.dataSource.data[index].show
		this.onToggleViewClicked.next([index, this.dataSource.data[index].show])
	}

	focusView(word: string) {
		this.onFocusViewClicked.next(word)
	}
}
