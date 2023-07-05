import { Component, OnInit } from '@angular/core';
import { SessionService } from './core/session.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {

  title = 'NetME';
  appVersion = 'v1.2.0';

  constructor(private sessionService: SessionService) {
    this.sessionService.checkToken()
  }

  ngOnInit() {
    console.log('Welcome to', this.title, this.appVersion)
  }
}
