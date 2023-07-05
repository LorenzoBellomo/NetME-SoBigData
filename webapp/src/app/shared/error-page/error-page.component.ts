import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
	selector: 'error-page',
	templateUrl: './error-page.component.html',
	styleUrls: ['./error-page.component.css']
})
export class ErrorPageComponent implements OnInit {

	@Input() linkBack: string = '/netme'
	@Input() errorTitle: string = ''
	@Input() errorMessage: string = ''

	@Output() clickGoBack: EventEmitter<any> = new EventEmitter()

	constructor() { }

	ngOnInit(): void {
	}

	onClickGoBack() {
		this.clickGoBack.emit(true)
	}

}
