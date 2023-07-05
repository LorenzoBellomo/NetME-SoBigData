import { Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { ResultsComponent } from '../results.component';
import { ResultsService } from '../results.service';

@Component({
	selector: 'console',
	templateUrl: './console.component.html',
	styleUrls: ['./console.component.css']
})
export class ConsoleComponent implements OnInit {

	@Input() id: string = ''
	@Input() resultReady: boolean = false
	consoleMessage: string = ''
	lastConsoleMessage: string = ''
	@Output() onClick: EventEmitter<any> = new EventEmitter()


	@ViewChild('scrollMe') private myScrollContainer: ElementRef | undefined;
	disableScrollDown: boolean = false;
	firstScroll: boolean = true;

	percentage: number = 0.0
	percentageStr: string = '0%'

	disableAnimation: boolean = true;

	constructor(private resultsService: ResultsService, private resultsComponent: ResultsComponent) { }

	ngOnInit(): void {
		this.resultsService.consoleMessages.forEach(s => this.addMessage(s))
		this.resultsComponent.lastConsoleMessage.subscribe(s => this.addMessage(s))
	}

	ngAfterViewChecked() {
		this.scrollToBottom()
	}

	ngAfterViewInit(): void {
		setTimeout(() => this.disableAnimation = false);
	}

	private addMessage(s: string) {
		const msg = s.split("||")
		this.lastConsoleMessage = msg[0]
		this.consoleMessage += msg[0] + '<br>'
		this.getPercentage(msg)
	}

	viewResult() {
		this.onClick.emit()
	}

	onScroll() {
		let element = this.myScrollContainer!.nativeElement
		let atBottom = element.scrollHeight - element.scrollTop === element.clientHeight
		if (atBottom) this.disableScrollDown = false
		else this.disableScrollDown = true
	}

	scrollToBottom(): void {
		if (this.disableScrollDown) return
		try {
			this.myScrollContainer!.nativeElement.scrollTop = this.myScrollContainer!.nativeElement.scrollHeight;
		} catch (err) { }
	}

	getPercentage(message: string[]): string {
		this.percentage = 0.0
		if (!message || message.length < 2) return "0%"
		try {
			this.percentage = parseFloat(message[1]) * 100
		} catch (error) { }

		this.percentageStr = this.percentage.toFixed(0) + "%"
		return this.percentageStr
	}

}
