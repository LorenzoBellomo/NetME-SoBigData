import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, Resolve, RouterStateSnapshot } from '@angular/router';
import { forkJoin, Observable, of } from 'rxjs';
import { DatabaseService } from './database.service';
import { ConfigMessage } from './models/config-message.model';

@Injectable({
    providedIn: 'root'
})
export class HomeConfigResolver implements Resolve<any> {
    constructor(private ds: DatabaseService) { }

    resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Promise<ConfigMessage[]> {
        return this.ds.loadConfig('home');
    }
}


@Injectable({
    providedIn: 'root'
})
export class ResultsConfigResolver implements Resolve<any> {
    constructor(private ds: DatabaseService) { }

    resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Promise<ConfigMessage[]> {
        return this.ds.loadConfig('results');
    }
}