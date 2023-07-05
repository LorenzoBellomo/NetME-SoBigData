import { trigger, transition, style, animate } from '@angular/animations';
import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'tt-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.css'],
  animations: [trigger('fadeIn', [transition(':enter', [style({ opacity: 0 }), animate('0.2s ease-out', style({ opacity: 1 }))])])]
})
export class PopupComponent implements OnInit {

  @Input() text: string = '';
  @Input() tip: string = '';
  isOver: boolean = false;

  constructor() { }

  ngOnInit(): void {
  }

}
