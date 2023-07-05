import { Component, Input, OnInit } from '@angular/core';
import { ConfigMessage } from 'src/app/core/models/config-message.model';

@Component({
  selector: 'message-info',
  templateUrl: './message-info.component.html',
  styleUrls: ['./message-info.component.css']
})
export class MessageInfoComponent implements OnInit {

  @Input() configMessage: ConfigMessage = { severity: 'info', message: '' }

  constructor() { }

  ngOnInit(): void {
  }

}
