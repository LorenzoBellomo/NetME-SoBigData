import { Component, OnInit, ViewChild } from '@angular/core';
import { Search } from '../../core/models/search.model';
import { SessionService } from '../../core/session.service';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';

@Component({
	selector: 'app-latest',
	templateUrl: './latest.component.html',
	styleUrls: ['./latest.component.css']
})
export class LatestComponent implements OnInit {

	dataSource = new MatTableDataSource<Search>();
	tableColumns: string[] = ['searchId', 'generatedOn', 'description', 'sources', 'delete'];

	latest: Search[] = []

	paginator: MatPaginator | undefined;


	constructor(private sessionService: SessionService) { }

	@ViewChild(MatSort) set matSort(ms: MatSort) {
		this.dataSource.sort = ms;
		this.setDataSourceAttributes();

	}

	@ViewChild(MatPaginator) set matPaginator(mp: MatPaginator) {
		this.paginator = mp;
		this.setDataSourceAttributes();
	}

	setDataSourceAttributes() {
		this.dataSource.paginator = this.paginator!;
	}

	ngOnInit(): void {
		this.sessionService.loadLatestSearch().then(v => {
			if (v) this.latest = (v as unknown as Search[]).reverse()
			this.dataSource.data = this.latest
		})
	}

	scrollToTop() {}

  deleteNetwork(id:string){
      this.sessionService.deleteItem(id)
      for(const idx in this.latest){
          const record = this.latest[idx]
          if(record["searchId"] != id) continue
          this.latest.splice(parseInt(idx), 1)
          this.dataSource.data = this.latest
          break
      }
      this.sessionService.updateItems(this.latest)
  }

}
