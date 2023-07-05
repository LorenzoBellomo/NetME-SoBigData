import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Category } from 'src/app/core/models/category.model';

@Component({
	selector: 'category-picker',
	templateUrl: './category-picker.component.html',
	styleUrls: ['./category-picker.component.css']
})
export class CategoryPickerComponent implements OnInit {

	@Input() categories: Category[] = []
	@Input() palette: string[] = []

	@Output() onToggleViewClicked: EventEmitter<any> = new EventEmitter();

	constructor() { }

	ngOnInit(): void { }

	toggleView(index: number) {
		this.categories[index].show = !this.categories[index].show
		this.onToggleViewClicked.next(this.categories)
	}

	getTextColor(color: string): string {
		const l = "#222"
		const d = "#eee"

		color = color.substring(1);
		var rgb = parseInt(color, 16);
		var r = (rgb >> 16) & 0xff;
		var g = (rgb >> 8) & 0xff;
		var b = (rgb >> 0) & 0xff;

		var luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
		if (luma >= 120) return l

		return d
	}

}
