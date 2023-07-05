import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit {

  menuOpen: boolean = false;

  constructor(private router: Router) {
    this.router.events.pipe(filter(r => r instanceof NavigationEnd)).subscribe(r => {
      this.menuOpen = false
    });
  }

  ngOnInit(): void {
  }

}
